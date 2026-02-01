from flask import Blueprint, request, jsonify
from ..db import get_db


hr_roles_bp = Blueprint('hr_roles', __name__)

@hr_roles_bp.route('/hr/roles/job-roles', methods=['GET'])
def list_job_roles():
    db = get_db()
    roles = db.job_roles.find({})
    # roles is now a list (JsonDB.find returns list)
    return jsonify(roles)

# Note: Other POST methods omitted for brevity as user requested specific flow functionality, 
# but could be added similarly easily.
