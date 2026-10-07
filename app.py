"""
Compliance Audit Checklist - Flask Application

Interactive compliance tool for Kenya DPA, banking, and telecom sectors.
"""

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///compliance.db'
db = SQLAlchemy(app)


class ComplianceItem(db.Model):
    """Individual compliance checklist item"""
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100))
    requirement = db.Column(db.String(500))
    standard = db.Column(db.String(50))  # DPA, CBK, ISO 27001
    completed = db.Column(db.Boolean, default=False)
    evidence_file = db.Column(db.String(500))
    owner = db.Column(db.String(100))
    due_date = db.Column(db.DateTime)
    created_date = db.Column(db.DateTime, default=datetime.now)


class AuditSession(db.Model):
    """Audit session tracking"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    start_date = db.Column(db.DateTime, default=datetime.now)
    end_date = db.Column(db.DateTime)
    auditor = db.Column(db.String(100))
    status = db.Column(db.String(50))  # In Progress, Completed
    compliance_score = db.Column(db.Float)


COMPLIANCE_STANDARDS = {
    "DPA": {
        "Data Protection": [
            "Personal data collection documented",
            "Lawful basis established",
            "Data minimization applied",
            "Purpose limitation enforced"
        ],
        "Individual Rights": [
            "Access requests handled within 30 days",
            "Correction mechanisms in place",
            "Deletion procedures documented",
            "Consent clearly obtained"
        ],
        "Breach Response": [
            "Breach detection process",
            "72-hour notification procedure",
            "Breach register maintained",
            "Root cause analysis completed"
        ]
    },
    "CBK": {
        "Account Security": [
            "Multi-factor authentication",
            "Account lockout procedures",
            "Session timeout controls",
            "Transaction limits enforced"
        ],
        "Data Security": [
            "Encryption for data in transit",
            "Encryption for data at rest",
            "Key management procedures",
            "Secure deletion procedures"
        ]
    },
    "ISO 27001": {
        "Access Control": [
            "User access reviews",
            "Privileged access management",
            "Password policy compliance",
            "Segregation of duties"
        ],
        "Incident Management": [
            "Incident classification",
            "Response procedures",
            "Escalation paths",
            "Post-incident review"
        ]
    }
}


@app.route('/')
def index():
    """Dashboard view"""
    total_items = ComplianceItem.query.count()
    completed_items = ComplianceItem.query.filter_by(completed=True).count()
    compliance_rate = (completed_items / total_items * 100) if total_items > 0 else 0
    
    return jsonify({
        "total_requirements": total_items,
        "completed": completed_items,
        "compliance_rate": f"{compliance_rate:.1f}%",
        "status": "Audit in progress" if compliance_rate < 100 else "Compliant"
    })


@app.route('/api/checklist/<category>')
def get_checklist(category):
    """Get checklist for standard"""
    if category in COMPLIANCE_STANDARDS:
        items = []
        for section, requirements in COMPLIANCE_STANDARDS[category].items():
            for req in requirements:
                db_item = ComplianceItem.query.filter_by(
                    standard=category,
                    requirement=req
                ).first()
                
                items.append({
                    "requirement": req,
                    "section": section,
                    "completed": db_item.completed if db_item else False,
                    "owner": db_item.owner if db_item else None
                })
        
        return jsonify({"standard": category, "items": items})
    return jsonify({"error": "Standard not found"}), 404


@app.route('/api/mark-complete/<int:item_id>', methods=['POST'])
def mark_complete(item_id):
    """Mark item as completed"""
    item = ComplianceItem.query.get(item_id)
    if item:
        item.completed = request.json.get('completed', False)
        item.owner = request.json.get('owner', item.owner)
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"error": "Item not found"}), 404


@app.route('/api/export-report')
def export_report():
    """Export compliance report"""
    items = ComplianceItem.query.all()
    report = {
        "generated": datetime.now().isoformat(),
        "total": len(items),
        "completed": sum(1 for i in items if i.completed),
        "compliance_rate": sum(1 for i in items if i.completed) / len(items) * 100 if items else 0,
        "by_standard": {}
    }
    
    for standard in ["DPA", "CBK", "ISO 27001"]:
        std_items = [i for i in items if i.standard == standard]
        report["by_standard"][standard] = {
            "total": len(std_items),
            "completed": sum(1 for i in std_items if i.completed),
            "compliance": sum(1 for i in std_items if i.completed) / len(std_items) * 100 if std_items else 0
        }
    
    return jsonify(report)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
