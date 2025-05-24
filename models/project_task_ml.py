import logging
import requests
from odoo import models, fields

_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    _inherit = 'project.task'

    task_complexity = fields.Integer('Task Complexity')
    team_size = fields.Integer("Team Size")
    effective_hours_custom = fields.Float("Effective Hours")
    predicted_cost = fields.Float('Predicted Cost', readonly=True)
    predicted_duration = fields.Float('Predicted Duration (Days)', readonly=True)  # ✅ NEW
    ml_status = fields.Char('ML Status', readonly=True)

    def action_call_ml_api(self):
        for task in self:
            experience = 0
            if task.user_ids:
                first_user = task.user_ids[0]
                experience = getattr(first_user.employee_id, 'experience', 0) if first_user.employee_id else 0

            payload = {
                "task_complexity": task.task_complexity or 0,
                "team_size": len(task.child_ids),
                "effective_hours": task.effective_hours_custom or 10.0,
                "experience": experience
            }

            try:
                res = requests.post("http://localhost:8000/api/project/predict", json=payload, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    if data.get('success'):
                        task.predicted_cost = data.get('predicted_cost', 0.0)
                        task.predicted_duration = data.get('predicted_duration', 0.0)
                        task.ml_status = "Prediction successful"
                    else:
                        task.ml_status = f"ML error: {data.get('error')}"
                else:
                    task.ml_status = f"HTTP error: {res.status_code}"
            except Exception as e:
                _logger.error(f"Failed to call ML API: {e}", exc_info=True)
                task.ml_status = "Connection error"