from . import db
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        return f"id: {self.id}, login: {self.login}"

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Sex(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(20), unique=True, nullable=False)


class ExperienceLevel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50), unique=True, nullable=False)


class InvolvementType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50), unique=True, nullable=False)


class ConditionType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50), unique=True, nullable=False)


class TargetType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), unique=True, nullable=False)


class RoleType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), unique=True, nullable=False)


class StageType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), unique=True, nullable=False)


class ProjectScopeType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), unique=True, nullable=False)


class ProjectTargetType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), unique=True, nullable=False)


class ProjectStageType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50), unique=True, nullable=False)


class ProjectConditionsType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50), unique=True, nullable=False)

class StatusInvite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(30), unique=True, nullable=False)


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    avatar = db.Column(db.String(255))
    name = db.Column(db.String(50))
    surname = db.Column(db.String(50))
    middlename = db.Column(db.String(50))
    birth_date = db.Column(db.DateTime)

    sex_id = db.Column(db.Integer, db.ForeignKey("sex.id"))
    sex = db.relationship("Sex")

    role_id = db.Column(db.Integer, db.ForeignKey("role_type.id"))
    role = db.relationship("RoleType")

    experience_id = db.Column(db.Integer, db.ForeignKey("experience_level.id"))
    experience = db.relationship("ExperienceLevel")

    involvement_id = db.Column(db.Integer, db.ForeignKey("involvement_type.id"))
    involvement = db.relationship("InvolvementType")

    conditions_id = db.Column(db.Integer, db.ForeignKey("condition_type.id"))
    conditions = db.relationship("ConditionType")

    target_id = db.Column(db.Integer, db.ForeignKey("target_type.id"))
    target = db.relationship("TargetType")

    scope_id = db.Column(db.Integer, db.ForeignKey('project_scope_type.id'))
    scope = db.relationship("ProjectScopeType")

    phone = db.Column(db.String(20))
    telegram_nickname = db.Column(db.String(50))
    portfolio_link = db.Column(db.String(200))
    about = db.Column(db.String(512))
    about_project = db.Column(db.String(512))

    def __repr__(self):
        return f"id: {self.id}, user_id: {self.user_id}, name: {self.name}, surname: {self.surname}"


class Owner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    avatar = db.Column(db.String(255))
    name = db.Column(db.String(50))
    surname = db.Column(db.String(50))
    middlename = db.Column(db.String(50))
    birth_date = db.Column(db.DateTime)

    sex_id = db.Column(db.Integer, db.ForeignKey("sex.id"))
    sex = db.relationship("Sex")

    role_id = db.Column(db.Integer, db.ForeignKey("role_type.id"))
    role = db.relationship("RoleType")

    experience_id = db.Column(db.Integer, db.ForeignKey("experience_level.id"))
    experience = db.relationship("ExperienceLevel")

    about = db.Column(db.String(512))

    def __repr__(self):
        return f"id: {self.id}, user_id: {self.user_id}, name: {self.name}, surname: {self.surname}"

class Favourite_employees(db.Model):
    id =  db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("owner.id"), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False)

    def __repr__(self):
        return f"id: {self.id}, owner_id: {self.owner_id}, employee_id: {self.employee_id}"


class Project(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    owner_id    = db.Column(db.Integer, db.ForeignKey("owner.id", ondelete="CASCADE"), nullable=False)
    owner = db.relationship("Owner", backref=db.backref("projects", cascade="all, delete-orphan"))                        

    title       = db.Column(db.String(100),  nullable=False)
    about       = db.Column(db.String(2000))

    stage_id      = db.Column(db.Integer, db.ForeignKey("project_stage_type.id"), nullable=False)
    stage         = db.relationship("ProjectStageType", backref="projects")

    conditions_id = db.Column(db.Integer, db.ForeignKey("project_conditions_type.id"), nullable=False)
    conditions    = db.relationship("ProjectConditionsType", backref="projects")

    target_id     = db.Column(db.Integer, db.ForeignKey("project_target_type.id"), nullable=False)
    target        = db.relationship("ProjectTargetType", backref="projects")

    scope_id      = db.Column(db.Integer, db.ForeignKey("project_scope_type.id"), nullable=True)
    scope         = db.relationship("ProjectScopeType", backref="projects")

    employee_description = db.Column(db.String(1000))

    def __repr__(self):
        return ( f"<Project id={self.id} title='{self.title}' " f"owner_id={self.owner_id} stage={self.stage.label}>")


class ProjectRoles(db.Model):
    id =  db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("role_type.id"), nullable=False)

    def __repr__(self):
        return f"id: {self.id}, project_id: {self.project_id}, role_id: {self.role_id}"


class ProjectEmployee(db.Model):
    id =  db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False)

    def __repr__(self):
        return f"id: {self.id}, project_id: {self.project_id}, employee: {self.employee_id}"


class Favourite_projects(db.Model):
    id =  db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False)

    def __repr__(self):
        return f"id: {self.id}, project_id: {self.project_id}, employee_id: {self.employee_id}"


class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False)

    status_id = db.Column(db.Integer, db.ForeignKey("status_invite.id"), nullable=False)
    status = db.relationship("StatusInvite", backref="responses")

    def __repr__(self):
        return (f"id: {self.id}, project_id: {self.project_id}, "
                f"employee_id: {self.employee_id}, status: {self.status.label}")


class Invite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)

    status_id = db.Column(db.Integer, db.ForeignKey("status_invite.id"), nullable=False)
    status = db.relationship("StatusInvite", backref="invites")

    checked = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return (f"id: {self.id}, project_id: {self.project_id}, "
                f"employee_id: {self.employee_id}, status: {self.status.label}")