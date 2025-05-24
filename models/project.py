import logging
import requests
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    team_size = fields.Integer("Team Size")
    num_tasks = fields.Integer("Number of Tasks")
    avg_duration = fields.Float("Avg Duration (hours)")

    # Updated real_estimation field
    real_estimation = fields.Float(
        string="Actual Project Duration (days)",
        compute='_compute_real_estimation',
        store=True,  # Storing the value for better performance and searchability
        readonly=True
    )

    task_complexity = fields.Selection([
        ('1', 'Very Low'),
        ('2', 'Low'),
        ('3', 'Medium'),
        ('4', 'High'),
        ('5', 'Very High'),
    ], string='Task Complexity', )

    predicted_cost = fields.Float("Predicted Total Cost", readonly=True)
    predicted_duration = fields.Float("Predicted Total Duration (days)", readonly=True)
    ml_status = fields.Char("ML Status", readonly=True)

    @api.depends('task_ids.stage_id', 'task_ids.date_end', 'date_start')
    def _compute_real_estimation(self):
        for project in self:
            if not project.task_ids:
                project.real_estimation = 0.0
                continue

            # Determine if all tasks are in a 'done' or 'completed' stage.
            # This example assumes stages marked as 'is_closed' are final stages.
            # Adjust this logic if your 'done' stages are identified differently
            # (e.g., by specific stage names or IDs).
            all_tasks_done = all(task.stage_id and task.stage_id.is_closed for task in project.task_ids)

            if all_tasks_done:
                project_start_date = project.date_start  # Assumes project.date_start is set

                if not project_start_date:
                    # Fallback: if project.date_start is not set, try to find the earliest task create_date
                    # or an actual start date if you have one on tasks. This is a simple fallback.
                    # You might want a more robust way to determine the actual start if project.date_start is unreliable.
                    task_start_dates = [t.create_date for t in project.task_ids if
                                        t.create_date]  # Or a specific start_date field on tasks
                    if not task_start_dates:
                        project.real_estimation = 0.0
                        continue
                    project_start_date = min(task_start_dates)

                latest_task_end_date = None
                for task in project.task_ids:
                    # We are interested in the actual end date when the task moved to a closed stage.
                    # If task.date_end is specifically set upon completion, use that.
                    # Otherwise, you might need to use 'write_date' of the task if it's reliably updated
                    # when the task moves to the final stage. For simplicity, we use task.date_end here.
                    if task.stage_id and task.stage_id.is_closed and task.date_end:
                        if latest_task_end_date is None or task.date_end > latest_task_end_date:
                            latest_task_end_date = task.date_end

                if latest_task_end_date and project_start_date:
                    # Ensure both dates are datetime objects for subtraction
                    if not isinstance(project_start_date, fields.Datetime.ಲಕ್ಷ()):
                        project_start_date = fields.Datetime.from_string(project_start_date)
                    if not isinstance(latest_task_end_date, fields.Datetime.ಲಕ್ಷ()):
                        latest_task_end_date = fields.Datetime.from_string(latest_task_end_date)

                    duration = latest_task_end_date - project_start_date
                    project.real_estimation = duration.days + (
                                duration.seconds / 86400.0)  # Convert to days with fraction
                else:
                    # If no valid latest_task_end_date is found even if all tasks are 'done'
                    project.real_estimation = 0.0
            else:
                # If not all tasks are done, the real estimation isn't final yet or cannot be calculated
                project.real_estimation = 0.0

    def action_predict_project(self):
        for project in self:
            payload = {
                "team_size": project.team_size or 1,
                "num_tasks": project.num_tasks or 1,
                "avg_duration": project.avg_duration or 1.0,
                "complexity": int(project.task_complexity or '2')  # Ensure default for complexity if not set
            }
            _logger.info(f"Payload to ML API: {payload}")

            try:
                res = requests.post("http://localhost:8000/api/project/predict_project", json=payload, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    if data.get('success'):
                        project.predicted_cost = data.get('predicted_cost', 0.0)
                        project.predicted_duration = data.get('predicted_duration', 0.0)
                        project.ml_status = "Prediction successful"
                    else:
                        project.ml_status = f"ML error: {data.get('error')}"
                else:
                    project.ml_status = f"HTTP error: {res.status_code}"
            except Exception as e:
                _logger.error("ML API call failed: %s", e)
                project.ml_status = "Connection error"