import os
from flask import send_file, Blueprint, request, redirect, url_for, render_template, flash, current_app, session, jsonify
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user, login_user, logout_user
import pandas as pd
from io import BytesIO
from app import db
from app.models import User, Employee, Owner, RoleType, ExperienceLevel, Sex, InvolvementType, ConditionType, TargetType, ProjectRoles, Favourite_projects, Response
from app.models import ProjectScopeType, Favourite_employees, ProjectTargetType, ProjectStageType, ProjectConditionsType, Project, ProjectEmployee, Invite, StatusInvite
from app import login_manager 
from app.file_utils import allowed_file, unique_filename
from datetime import datetime
from sqlalchemy import func, not_

main_bp = Blueprint('main', __name__)

login_manager.login_view = 'main.home'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

"""
Обрабатывает корневой маршрут. Перенаправляет на выбор типа пользователя или дашборд,
в зависимости от того, зарегистрирован ли пользователь как сотрудник или владелец.
"""
@main_bp.route('/')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('main.login'))

    owner_exists = Owner.query.filter_by(user_id=current_user.id).first()
    employee_exists = Employee.query.filter_by(user_id=current_user.id).first()  

    if not owner_exists and not employee_exists:
        return redirect(url_for('main.type_user'))
    else:
        if owner_exists:
            return redirect(url_for('main.general'))
        elif employee_exists:
            return redirect(url_for('main.general'))
        else:
            flash('Непредвиденная ошибка.', 'warning')


"""
Отображает страницу входа. Обрабатывает отправку формы и логин пользователя.
"""
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Пожалуйста, заполните оба поля.', 'warning')
            return render_template('login.html', login=True)

        user = User.query.filter_by(login=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.home'))
        else:
            flash('Неверный email или пароль.', 'danger')

    return render_template('login.html', login=True)


"""
Обрабатывает регистрацию нового пользователя. Создает нового User и выполняет вход.
"""
@main_bp.route('/registration', methods=['GET', 'POST'])
def registration():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not email or not password:
            flash('Пожалуйста, заполните все поля.', 'warning')
            return render_template('login.html')

        existing_user = User.query.filter_by(login=email).first()
        if existing_user:
            flash('Пользователь с таким email уже зарегистрирован.', 'danger')
            return render_template('login.html')

        new_user = User(login=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('main.home'))

    return render_template('login.html')


"""
Выход пользователя из системы и редирект на домашнюю страницу.
"""
@main_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))

"""
Позволяет авторизованному пользователю выбрать тип — сотрудник или владелец.
Создает соответствующую запись в таблице Employee или Owner.
"""
@main_bp.route('/type_user', methods=['GET', 'POST'])
@login_required
def type_user():
    if request.method == 'POST':
        user_type = request.form.get('user_type')

        if user_type == "employee":
            employee = Employee(user_id=current_user.id)
            db.session.add(employee)
            db.session.commit()
            return redirect(url_for('main.home'))

        elif user_type == "owner":
            owner = Owner(user_id=current_user.id)
            db.session.add(owner)
            db.session.commit()
            return redirect(url_for('main.home'))

        else:
            flash('Непредвиденная ошибка.', 'warning')

    return render_template('type_user.html')


"""
Главная страница дашборда. Если пользователь — владелец, отображает сотрудников для подбора команды.
Если пользователь — сотрудник, отображает доступные проекты. Включает фильтрацию и избранное.
"""
@main_bp.route('/general', methods=['GET', 'POST'])
@login_required
def general():
    owner_exists = Owner.query.filter_by(user_id=current_user.id).first()
    employee_exists = Employee.query.filter_by(user_id=current_user.id).first()
    count_notifications = None
    roles = RoleType.query.all()
    scopes = ProjectScopeType.query.all()

    if owner_exists:
        count_notifications = (
            db.session.query(func.count(Invite.id))
            .join(Project, Project.id == Invite.project_id)
            .join(StatusInvite, StatusInvite.id == Invite.status_id)
            .filter(Project.owner_id == owner_exists.id)
            .filter(StatusInvite.label == "Отправлен")
            .scalar()
        )
        if count_notifications > 100:
            count_notifications = "99+"
        experiences = ExperienceLevel.query.all()
        involvements = InvolvementType.query.all()
        conditionss = ConditionType.query.all()
        targets = TargetType.query.all()

        employees = Employee.query.all()

        favourites = Favourite_employees.query.filter_by(owner_id=owner_exists.id).all()
        fav_ids = {fav.employee_id for fav in favourites}
        for emp in employees:
            emp.fav = emp.id in fav_ids

        return render_template('general.html', owner=True, count_notifications=count_notifications, roles=roles,
        conditionss=conditionss, scopes=scopes, experiences=experiences, involvements=involvements, targets=targets,
        employees=employees)
    elif employee_exists:
        count_notifications = (
            db.session.query(func.count(Invite.id))
            .join(StatusInvite, StatusInvite.id == Invite.status_id)
            .filter(Invite.employee_id == employee_exists.id)
            .filter(StatusInvite.label == "Отправлен")
            .scalar(
        ))
        if count_notifications > 100:
            count_notifications = "99+"
        conditionss = ProjectConditionsType.query.all()
        targets = ProjectTargetType.query.all()
        stages = ProjectStageType.query.all()

        projects = Project.query.all()
        favourites = Favourite_projects.query.filter_by(employee_id=employee_exists.id).all()
        fav_project_ids = {fav.project_id for fav in favourites}
        for project in projects:
            project.fav = project.id in fav_project_ids
            project_roles = ProjectRoles.query.filter_by(project_id=project.id).all()
            role_labels = [RoleType.query.get(role.role_id).label for role in project_roles]
            project.roles_str = ', '.join(role_labels)

            project_employees = ProjectEmployee.query.filter_by(project_id=project.id).all()
            employees_info = []
            for pe in project_employees:
                employee = Employee.query.get(pe.employee_id)
                if employee:
                    full_name = f"{employee.name} {employee.surname}".strip()
                    employees_info.append((employee.id, full_name))

            project.employees = employees_info 

        return render_template('general.html', count_notifications=count_notifications, owner=False, roles=roles, scopes=scopes, stages=stages, targets=targets, conditionss=conditionss, projects=projects)
    else:
        pass


"""
Отображает страницу профиля текущего пользователя (владельца или сотрудника).
Показывает информацию и связанные проекты, отклики или приглашения.
"""
@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    count_notifications = None
    owner_exists = Owner.query.filter_by(user_id=current_user.id).first()
    employee_exists = Employee.query.filter_by(user_id=current_user.id).first()
    if owner_exists:
        count_notifications = (
            db.session.query(func.count(Invite.id))
            .join(Project, Project.id == Invite.project_id)
            .join(StatusInvite, StatusInvite.id == Invite.status_id)
            .filter(Project.owner_id == owner_exists.id)
            .filter(StatusInvite.label == "Отправлен")
            .scalar()
        )
        if count_notifications > 100:
            count_notifications = "99+"
        data = Owner.query.filter_by(user_id=current_user.id).first()
        projects = Project.query.filter_by(owner_id=owner_exists.id).all()
        for project in projects:
            project_roles = ProjectRoles.query.filter_by(project_id=project.id).all()
            role_labels = [RoleType.query.get(role.role_id).label for role in project_roles]
            project.roles_str = ', '.join(role_labels)

            project_employees = ProjectEmployee.query.filter_by(project_id=project.id).all()
            employees_info = []
            for pe in project_employees:
                employee = Employee.query.get(pe.employee_id)
                if employee:
                    full_name = f"{employee.name} {employee.surname}".strip()
                    employees_info.append((employee.id, full_name))

            project.employees = employees_info
            project.invites = Response.query.filter_by(project_id=project.id).count()

        return render_template('profile.html', owner=True, count_notifications=count_notifications, data=data, projects=projects)
    elif employee_exists:
        count_notifications = (
            db.session.query(func.count(Invite.id))
            .join(StatusInvite, StatusInvite.id == Invite.status_id)
            .filter(Invite.employee_id == employee_exists.id)
            .filter(StatusInvite.label == "Отправлен")
            .scalar(
        ))
        if count_notifications > 100:
            count_notifications = "99+"
        data = Employee.query.filter_by(user_id=current_user.id).first() 

        responses = Response.query.filter_by(employee_id=employee_exists.id).all()
        project_ids = [r.project_id for r in responses]
        projects = Project.query.filter(Project.id.in_(project_ids)).all()
        for project in projects:
            project_roles = ProjectRoles.query.filter_by(project_id=project.id).all()
            role_labels = [RoleType.query.get(role.role_id).label for role in project_roles]
            project.roles_str = ', '.join(role_labels)

            project_employees = ProjectEmployee.query.filter_by(project_id=project.id).all()
            employees_info = []
            for pe in project_employees:
                employee = Employee.query.get(pe.employee_id)
                if employee:
                    full_name = f"{employee.name} {employee.surname}".strip()
                    employees_info.append((employee.id, full_name))

            project.employees = employees_info
            project.invite = Response.query.filter_by(project_id=project.id, employee_id=employee_exists.id).first()

        return render_template('profile.html', owner=False, count_notifications=count_notifications, data=data, projects=projects)
    else:
        pass


"""
Позволяет владельцу или сотруднику редактировать свой профиль.
Обрабатывает загрузку аватара, валидацию даты и обновление связанных полей.
"""
@main_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    count_notifications = None
    owner_exists = Owner.query.filter_by(user_id=current_user.id).first()
    employee_exists = Employee.query.filter_by(user_id=current_user.id).first()
    if request.method == 'POST':
        if owner_exists:
            owner_exists.surname     = request.form.get('surname', '').strip()
            owner_exists.name        = request.form.get('name', '').strip()
            owner_exists.middlename  = request.form.get('middlename', '').strip()
            owner_exists.about  = request.form.get('about', '').strip()

            owner_exists.role_id      = request.form.get('role_id') or None
            owner_exists.experience_id = request.form.get('experience_id') or None
            owner_exists.sex_id       = request.form.get('sex_id') or None

            owner_exists.role       = RoleType.query.get(owner_exists.role_id)
            owner_exists.experience = ExperienceLevel.query.get(owner_exists.experience_id)
            owner_exists.sex        = Sex.query.get(owner_exists.sex_id)

            birth_date_str = request.form.get('birth_date', '').strip()
            try:
                owner_exists.birth_date = datetime.strptime(birth_date_str, '%d.%m.%Y') if birth_date_str else None
            except ValueError:
                flash('Неверный формат даты. Используйте ДД.ММ.ГГГГ', 'error')
                return redirect(url_for('main.edit_profile'))

            file = request.files.get('avatar')
            if file and file.filename and allowed_file(file.filename):
                filename = unique_filename(file.filename)
                path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(path)
                owner_exists.avatar = f"uploads/{filename}"
            
            db.session.commit()
            flash('Профиль обновлён', 'success')
            return redirect(url_for('main.profile'))
        if employee_exists:
            employee_exists.surname = request.form.get('surname', '').strip()
            employee_exists.name = request.form.get('name', '').strip()
            employee_exists.middlename = request.form.get('middlename', '').strip()
            employee_exists.about = request.form.get('about', '').strip()
            employee_exists.about_project = request.form.get('about_project', '').strip()
            employee_exists.portfolio_link = request.form.get('portfolio_link', '').strip()
            employee_exists.phone = request.form.get('phone', '').strip()
            employee_exists.telegram_nickname = request.form.get('telegram_nickname', '').strip()

            employee_exists.role_id = request.form.get('role_id') or None
            employee_exists.experience_id = request.form.get('experience_id') or None
            employee_exists.sex_id = request.form.get('sex_id') or None
            employee_exists.involvement_id = request.form.get('involvement_id') or None
            employee_exists.conditions_id = request.form.get('conditions_id') or None
            employee_exists.target_id = request.form.get('target_id') or None
            employee_exists.scope_id = request.form.get('scope_id') or None

            employee_exists.role = RoleType.query.get(employee_exists.role_id) if employee_exists.role_id else None
            employee_exists.experience = ExperienceLevel.query.get(employee_exists.experience_id) if employee_exists.experience_id else None
            employee_exists.sex = Sex.query.get(employee_exists.sex_id) if employee_exists.sex_id else None
            employee_exists.involvement = InvolvementType.query.get(employee_exists.involvement_id) if employee_exists.involvement_id else None
            employee_exists.conditions = ConditionType.query.get(employee_exists.conditions_id) if employee_exists.conditions_id else None
            employee_exists.target = TargetType.query.get(employee_exists.target_id) if employee_exists.target_id else None
            employee_exists.scope = ProjectScopeType.query.get(employee_exists.scope_id) if employee_exists.scope_id else None


            birth_date_str = request.form.get('birth_date', '').strip()
            try:
                employee_exists.birth_date = datetime.strptime(birth_date_str, '%d.%m.%Y') if birth_date_str else None
            except ValueError:
                flash('Неверный формат даты. Используйте ДД.ММ.ГГГГ', 'error')
                return redirect(url_for('main.edit_profile'))

            file = request.files.get('avatar')
            if file and file.filename and allowed_file(file.filename):
                filename = unique_filename(file.filename)
                path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(path)
                employee_exists.avatar = f"uploads/{filename}"

            db.session.commit()
            flash('Профиль обновлён', 'success')
            return redirect(url_for('main.profile'))
            pass

    roles = RoleType.query.all()
    experiences = ExperienceLevel.query.all()
    sexs = Sex.query.all()
    if owner_exists:
        count_notifications = (
            db.session.query(func.count(Invite.id))
            .join(Project, Project.id == Invite.project_id)
            .join(StatusInvite, StatusInvite.id == Invite.status_id)
            .filter(Project.owner_id == owner_exists.id)
            .filter(StatusInvite.label == "Отправлен")
            .scalar()
        )
        if count_notifications > 100:
            count_notifications = "99+"
        data = Owner.query.filter_by(user_id=current_user.id).first()
        return render_template('edit_profile.html', count_notifications=count_notifications, owner=True, data=data, roles=roles, experiences=experiences, sexs=sexs)
    elif employee_exists:
        count_notifications = (
            db.session.query(func.count(Invite.id))
            .join(StatusInvite, StatusInvite.id == Invite.status_id)
            .filter(Invite.employee_id == employee_exists.id)
            .filter(StatusInvite.label == "Отправлен")
            .scalar(
        ))
        if count_notifications > 100:
            count_notifications = "99+"
        involvements = InvolvementType.query.all()
        conditionss = ConditionType.query.all()
        targets = TargetType.query.all()
        scopes = ProjectScopeType.query.all()

        data = Employee.query.filter_by(user_id=current_user.id).first()  
        return render_template('edit_profile.html', count_notifications=count_notifications, owner=False, data=data, roles=roles, experiences=experiences, sexs=sexs,
        involvements=involvements, conditionss=conditionss, targets=targets, scopes=scopes)
    else:
        pass


"""
Отображает подробную страницу сотрудника.
Если текущий пользователь — владелец, показывает, в какие проекты его можно пригласить.
"""
@main_bp.route('/employee', methods=['GET', 'POST'])
@login_required
def employee():
    count_notifications = None
    project_yes = None
    emp_id = request.args.get('id')
    projects = None
    fav = None
    if emp_id:
        owner_exists = Owner.query.filter_by(user_id=current_user.id).first()
        employee = Employee.query.filter_by(id=emp_id).first()
        owner = False
        if employee:
            if owner_exists:
                count_notifications = (
                    db.session.query(func.count(Invite.id))
                    .join(Project, Project.id == Invite.project_id)
                    .join(StatusInvite, StatusInvite.id == Invite.status_id)
                    .filter(Project.owner_id == owner_exists.id)
                    .filter(StatusInvite.label == "Отправлен")
                    .scalar()
                )
                if count_notifications > 100:
                    count_notifications = "99+"
                owner = True

                response_project_ids = db.session.query(Response.project_id).filter_by(employee_id=emp_id)
                invite_project_ids = db.session.query(Invite.project_id).filter_by(employee_id=emp_id)
                assigned_project_ids = db.session.query(ProjectEmployee.project_id).filter_by(employee_id=emp_id)

                excluded_project_ids = response_project_ids.union(invite_project_ids).union(assigned_project_ids).subquery()

                projectYes = Project.query.filter_by(owner_id=owner_exists.id)
                if projectYes:
                    project_yes= True
                projects = (
                    Project.query
                    .filter(Project.owner_id == owner_exists.id)
                    .filter(~Project.id.in_(excluded_project_ids))
                    .all()
                )
                if projects:
                    for project in projects:
                        project_roles = ProjectRoles.query.filter_by(project_id=project.id).all()
                        role_labels = [RoleType.query.get(role.role_id).label for role in project_roles]
                        project.roles_str = ', '.join(role_labels)
                if Favourite_employees.query.filter_by(owner_id=owner_exists.id, employee_id=employee.id).first():
                    fav = True

            else:
                employee_exists = Employee.query.filter_by(user_id=current_user.id).first()
                count_notifications = (
                    db.session.query(func.count(Invite.id))
                    .join(StatusInvite, StatusInvite.id == Invite.status_id)
                    .filter(Invite.employee_id == employee_exists.id)
                    .filter(StatusInvite.label == "Отправлен")
                    .scalar(
                ))
                if count_notifications > 100:
                    count_notifications = "99+"
            return render_template('employee.html', projects=projects, count_notifications=count_notifications, owner=owner, employee=employee, fav=fav, project_yes=project_yes)
    else:
        return "No employee ID provided", 400


"""
Отображает подробную страницу создателя проекта.
Показывает, какие проекты есть.
"""
@main_bp.route('/owner', methods=['GET', 'POST'])
@login_required
def owner():
    count_notifications = None
    project_yes = None
    own_id = request.args.get('id')
    projects = None
    if own_id:
        owner_exists = Owner.query.filter_by(user_id=current_user.id).first()
        own_onj = Owner.query.filter_by(id=own_id).first()
        owner = False
        if own_onj:
            projects = Project.query.filter_by(owner_id=own_id).all()

            if projects:
                for project in projects:
                    project_roles = ProjectRoles.query.filter_by(project_id=project.id).all()
                    role_labels = [RoleType.query.get(role.role_id).label for role in project_roles]
                    project.roles_str = ', '.join(role_labels)
                    if not owner_exists:
                        employee = Employee.query.filter_by(user_id=current_user.id).first()
                        fav_project = Favourite_projects.query.filter_by(employee_id=employee.id, project_id=project.id).first()
                        print(fav_project)
                        if fav_project:
                            project.fav = True
                    project_employees = ProjectEmployee.query.filter_by(project_id=project.id).all()
                    employees_info = []
                    for pe in project_employees:
                        employee = Employee.query.get(pe.employee_id)
                        if employee:
                            full_name = f"{employee.name} {employee.surname}".strip()
                            employees_info.append((employee.id, full_name))
                    project.employees = employees_info 
            if owner_exists:
                count_notifications = (
                    db.session.query(func.count(Invite.id))
                    .join(Project, Project.id == Invite.project_id)
                    .join(StatusInvite, StatusInvite.id == Invite.status_id)
                    .filter(Project.owner_id == owner_exists.id)
                    .filter(StatusInvite.label == "Отправлен")
                    .scalar()
                )
                if count_notifications > 100:
                    count_notifications = "99+"
                owner = True

            else:
                employee_exists = Employee.query.filter_by(user_id=current_user.id).first()
                count_notifications = (
                    db.session.query(func.count(Invite.id))
                    .join(StatusInvite, StatusInvite.id == Invite.status_id)
                    .filter(Invite.employee_id == employee_exists.id)
                    .filter(StatusInvite.label == "Отправлен")
                    .scalar(
                ))
                if count_notifications > 100:
                    count_notifications = "99+"
            return render_template('owner.html', projects=projects, count_notifications=count_notifications, owner=owner, own_onj=own_onj)
    else:
        return "No employee ID provided", 400


"""
Добавляет или удаляет сотрудника из избранного текущего владельца по ID.
"""
@main_bp.route('/favourite_add', methods=['GET', 'POST'])
@login_required
def favourite_add():
    data = request.get_json()
    emp_id = data.get('id') if data else None
    if not emp_id:
        return jsonify(error="No employee ID provided"), 400

    owner = Owner.query.filter_by(user_id=current_user.id).first()
    if not owner:
        return jsonify(error="Недостаточно прав"), 403

    employee = Employee.query.get(emp_id)
    if not employee:
        return jsonify(error="Пользователь не найден"), 404

    fav = Favourite_employees.query.filter_by(owner_id=owner.id, employee_id=employee.id).first()
    try:
        if fav:
            db.session.delete(fav)
            action = "removed"
            message = "Сотрудник удалён из избранного"
        else:
            fav = Favourite_employees(owner_id=owner.id, employee_id=employee.id)
            db.session.add(fav)
            action = "added"
            message = "Сотрудник добавлен в избранное"

        db.session.commit()
        return jsonify(
            status="success",
            action=action,
            employee_id=employee.id,
            message=message,
        ), 200

    except Exception as exc:
        return jsonify(error="Database error"), 500


"""
Добавляет или удаляет проект из избранного текущего сотрудника.
"""
@main_bp.route('/favourite_project_add', methods=['POST'])
@login_required
def favourite_project_add():
    data = request.get_json()
    project_id = data.get('id') if data else None

    if not project_id:
        return jsonify(error="No project ID provided"), 400

    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if not employee:
        return jsonify(error="Вы не авторизованы как сотрудник"), 403

    project = Project.query.get(project_id)
    if not project:
        return jsonify(error="Проект не найден"), 404

    fav = Favourite_projects.query.filter_by(employee_id=employee.id, project_id=project.id).first()

    try:
        if fav:
            db.session.delete(fav)
            action = "removed"
            message = "Проект удалён из избранного"
        else:
            fav = Favourite_projects(employee_id=employee.id, project_id=project.id)
            db.session.add(fav)
            action = "added"
            message = "Проект добавлен в избранное"

        db.session.commit()
        return jsonify(
            status="success",
            action=action,
            project_id=project.id,
            message=message
        ), 200

    except Exception as exc:
        db.session.rollback()
        return jsonify(error="Ошибка базы данных"), 500


"""
Позволяет владельцу создать новый проект, указав параметры и требуемые роли.
"""
@main_bp.route('/project_add', methods=['GET', 'POST'])
@login_required
def project_add():
    count_notifications = None
    owner = Owner.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        if not owner:
            flash("Отказано в доступе", "error")
            return redirect(url_for('main.main'))

        title = request.form.get('title', '').strip()
        about_project = request.form.get('about', '').strip() 
        employee_description = request.form.get('employee_description', '').strip()

        stage_id = request.form.get('stage_id')
        conditions_id = request.form.get('conditions_id')
        target_id = request.form.get('target_id')
        scope_id = request.form.get('scope_id') or None

        project = Project(
            owner_id=owner.id,
            title=title,
            about=about_project,
            employee_description=employee_description,
            stage_id=stage_id,
            conditions_id=conditions_id,
            target_id=target_id,
            scope_id=scope_id
        )

        project.stage = ProjectStageType.query.get(stage_id) if stage_id else None
        project.conditions = ProjectConditionsType.query.get(conditions_id) if conditions_id else None
        project.target = ProjectTargetType.query.get(target_id) if target_id else None
        project.scope = ProjectScopeType.query.get(scope_id) if scope_id else None

        db.session.add(project)
        db.session.commit()

        role_ids = request.form.getlist('role_id')
        for role_id in role_ids:
            if role_id:
                pr = ProjectRoles(project_id=project.id, role_id=role_id)
                db.session.add(pr)

        db.session.commit()

        flash("Проект успешно создан!", "success")
        return redirect(url_for('main.general'))
    
    if owner:
        count_notifications = (
            db.session.query(func.count(Invite.id))
            .join(Project, Project.id == Invite.project_id)
            .join(StatusInvite, StatusInvite.id == Invite.status_id)
            .filter(Project.owner_id == owner.id)
            .filter(StatusInvite.label == "Отправлен")
            .scalar()
        )
        if count_notifications > 100:
            count_notifications = "99+"
        roles = RoleType.query.all()
        conditionss = ProjectConditionsType.query.all()
        scopes = ProjectScopeType.query.all()
        stages = ProjectStageType.query.all()
        targets = ProjectTargetType.query.all()
        return render_template('edit_project.html', count_notifications=count_notifications, owner=True, create=True, roles=roles, scopes=scopes, conditionss=conditionss, targets=targets, stages=stages)
    else:
        return redirect(url_for('main.home'))


"""
Позволяет владельцу редактировать существующий проект. Доступен только автору проекта.
"""
@main_bp.route('/edit_project', methods=['GET', 'POST'])
@login_required
def edit_project():
    count_notifications = None
    owner = Owner.query.filter_by(user_id=current_user.id).first()
    project_id = request.args.get('id')

    if not owner or not project_id:
        flash("Отказано в доступе", "error")
        return redirect(url_for('main.general'))

    project = Project.query.get(project_id)

    if not project or project.owner_id != owner.id:
        flash("Проект не найден или доступ запрещён", "error")
        return redirect(url_for('main.general'))

    if request.method == 'POST':
        project.title = request.form.get('title', '').strip()
        project.about = request.form.get('about', '').strip()
        project.employee_description = request.form.get('employee_description', '').strip()
        
        project.stage_id = request.form.get('stage_id')
        project.conditions_id = request.form.get('conditions_id')
        project.target_id = request.form.get('target_id')
        project.scope_id = request.form.get('scope_id') or None

        project.stage = ProjectStageType.query.get(project.stage_id) if project.stage_id else None
        project.conditions = ProjectConditionsType.query.get(project.conditions_id) if project.conditions_id else None
        project.target = ProjectTargetType.query.get(project.target_id) if project.target_id else None
        project.scope = ProjectScopeType.query.get(project.scope_id) if project.scope_id else None

        db.session.commit()
        ProjectRoles.query.filter_by(project_id=project.id).delete()

        role_ids = request.form.getlist('role_id')
        for role_id in role_ids:
            if role_id:
                pr = ProjectRoles(project_id=project.id, role_id=role_id)
                db.session.add(pr)

        db.session.commit()

        flash("Проект успешно обновлён!", "success")
        return redirect(url_for('main.profile'))
    
    count_notifications = (
        db.session.query(func.count(Invite.id))
        .join(Project, Project.id == Invite.project_id)
        .join(StatusInvite, StatusInvite.id == Invite.status_id)
        .filter(Project.owner_id == owner.id)
        .filter(StatusInvite.label == "Отправлен")
        .scalar()
    )
    if count_notifications > 100:
        count_notifications = "99+"
    project.roles = [pr.role_id for pr in ProjectRoles.query.filter_by(project_id=project.id).all()]
    roles = RoleType.query.all()
    conditionss = ProjectConditionsType.query.all()
    scopes = ProjectScopeType.query.all()
    stages = ProjectStageType.query.all()
    targets = ProjectTargetType.query.all()
    return render_template('edit_project.html', count_notifications=count_notifications, owner=True, create=False, project=project, roles=roles, scopes=scopes, conditionss=conditionss, targets=targets, stages=stages)


"""
Отображает страницу проекта с подробной информацией, ролями, участниками, откликами и приглашениями.
"""
@main_bp.route('/project', methods=['GET', 'POST'])
@login_required
def project():
    count_notifications = None
    project_id = request.args.get('id')
    if project_id:
        owner_exists = Owner.query.filter_by(user_id=current_user.id).first()
        owner = False
        if owner_exists:
            count_notifications = (
                db.session.query(func.count(Invite.id))
                .join(Project, Project.id == Invite.project_id)
                .join(StatusInvite, StatusInvite.id == Invite.status_id)
                .filter(Project.owner_id == owner_exists.id)
                .filter(StatusInvite.label == "Отправлен")
                .scalar()
            )
            if count_notifications > 100:
                count_notifications = "99+"
            owner = True
        else:
            employee_exists = Employee.query.filter_by(user_id=current_user.id).first()
            count_notifications = (
                db.session.query(func.count(Invite.id))
                .join(StatusInvite, StatusInvite.id == Invite.status_id)
                .filter(Invite.employee_id == employee_exists.id)
                .filter(StatusInvite.label == "Отправлен")
                .scalar(
            ))
            if count_notifications > 100:
                count_notifications = "99+"
        
        project = Project.query.filter_by(id=project_id).first()
        if project:
            project_roles = ProjectRoles.query.filter_by(project_id=project.id).all()
            role_labels = [RoleType.query.get(role.role_id).label for role in project_roles]
            project.roles_str = ', '.join(role_labels)

            creator = False
            if owner_exists and project.owner_id == owner_exists.id:
                creator = True

            project_employees = ProjectEmployee.query.filter_by(project_id=project.id).all()
            employees_info = []
            for pe in project_employees:
                employee = Employee.query.get(pe.employee_id)
                if employee:
                    full_name = f"{employee.name} {employee.surname}".strip()
                    employees_info.append((employee.id, full_name))
            project.employees = employees_info

            employee_exists = Employee.query.filter_by(user_id=current_user.id).first()
            fav = False
            response = None

            if employee_exists:
                favourites = Favourite_projects.query.filter_by(
                    project_id=project.id,
                    employee_id=employee_exists.id
                ).all()
                if favourites:
                    fav = True

                response = Response.query.filter_by(
                    project_id=project.id,
                    employee_id=employee_exists.id
                ).first()

                project.invite = Invite.query.filter_by(
                    project_id=project.id,
                    employee_id=employee_exists.id
                ).first()

                project.in_team = any(
                    pe.employee_id == employee_exists.id for pe in project_employees
                )

            employees = []
            if creator:
                responses = Response.query.filter_by(project_id=project.id).all()
                for re in responses:
                    emp = Employee.query.get(re.employee_id)
                    emp.response = re
                    employees.append(emp)

                favourites = Favourite_employees.query.filter_by(owner_id=owner_exists.id).all()
                fav_ids = {fav.employee_id for fav in favourites}
                for emp in employees:
                    emp.fav = emp.id in fav_ids

            return render_template('project.html', count_notifications=count_notifications, owner=owner, project=project, creator=creator, fav=fav, response=response, employees=employees)
    else:
        return "No employee ID provided", 400


"""
Позволяет сотруднику откликнуться на проект, создавая запись в таблице откликов.
"""
@main_bp.route('/add_response', methods=['GET', 'POST'])
@login_required
def add_response():
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    project_id = request.args.get('id')

    if not employee or not project_id:
        flash("Отказано в доступе", "error")
        return redirect(url_for('main.general'))

    project = Project.query.get(project_id)
    if not project:
        flash("Проект не найден", "error")
        return redirect(url_for('main.general'))

    existing_response = Response.query.filter_by(
        employee_id=employee.id,
        project_id=project.id
    ).first()

    if existing_response:
        flash("Вы уже откликнулись на этот проект", "info")
        return redirect(url_for('main.general'))

    status_sent = StatusInvite.query.filter_by(label="Отправлен").first()
    if not status_sent:
        flash("Статус 'Отправлен' не найден", "error")
        return redirect(url_for('main.general'))

    response = Response(
        employee_id=employee.id,
        project_id=project.id,
        status_id=status_sent.id
    )

    db.session.add(response)
    db.session.commit()

    flash("Заявка в проект успешно отправлена!", "success")
    return redirect(url_for('main.general'))


"""
Позволяет владельцу принять отклик сотрудника и добавить его в участники проекта.
"""
@main_bp.route('/ok_response', methods=['GET', 'POST'])
@login_required
def ok_response():
    owner_exists = Owner.query.filter_by(user_id=current_user.id).first()
    response_id = request.args.get('id')

    if not owner_exists or not response_id:
        flash("Отказано в доступе", "error")
        return redirect(url_for('main.general'))

    response = Response.query.get(response_id)
    if not response:
        flash("Отклик не найден", "error")
        return redirect(url_for('main.general'))

    project = Project.query.get(response.project_id)
    if not project:
        flash("Проект не найден", "error")
        return redirect(url_for('main.general'))

    if owner_exists.id != project.owner_id:
        flash("Отказано в доступе", "error")
        return redirect(url_for('main.general'))

    status_sent = StatusInvite.query.filter_by(label="Принят").first()
    if not status_sent:
        flash("Статус 'Принят' не найден", "error")
        return redirect(url_for('main.general'))

    response.status_id = status_sent.id
    response.status = status_sent

    projectemployee = ProjectEmployee(
        project_id=project.id,
        employee_id=response.employee_id
    )

    db.session.add(projectemployee)
    db.session.commit()

    flash("Заявка в проект успешно принята!", "success")
    return redirect(url_for('main.project', id=project.id))


"""
Позволяет владельцу отклонить отклик сотрудника.
"""
@main_bp.route('/no_response', methods=['GET', 'POST'])
@login_required
def no_response():
    owner_exists = Owner.query.filter_by(user_id=current_user.id).first()
    response_id = request.args.get('id')

    if not owner_exists or not response_id:
        flash("Отказано в доступе", "error")
        return redirect(url_for('main.general'))

    response = Response.query.get(response_id)
    if not response:
        flash("Отклик не найден", "error")
        return redirect(url_for('main.general'))

    project = Project.query.get(response.project_id)
    if not project:
        flash("Проект не найден", "error")
        return redirect(url_for('main.general'))

    if owner_exists.id != project.owner_id:
        flash("Отказано в доступе", "error")
        return redirect(url_for('main.general'))

    status_sent = StatusInvite.query.filter_by(label="Отклонён").first()
    if not status_sent:
        flash("Статус 'Отклонён' не найден", "error")
        return redirect(url_for('main.general'))

    response.status_id = status_sent.id
    response.status = status_sent

    db.session.commit()

    flash("Заявка в проект успешно отклонена!", "success")
    return redirect(url_for('main.project', id=project_id))


"""
Позволяет сотруднику отменить свой отклик на участие в проекте.
"""
@main_bp.route('/remove_response', methods=['POST', 'GET'])
@login_required
def remove_response():
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    project_id = request.args.get('id')

    if not employee or not project_id:
        flash("Отказано в доступе", "error")
        return redirect(url_for('main.general'))

    response = Response.query.filter_by(
        employee_id=employee.id,
        project_id=project_id
    ).first()

    if not response:
        flash("Заявка не найдена", "info")
        return redirect(url_for('main.profile'))

    db.session.delete(response)
    db.session.commit()

    flash("Заявка в проект успешно отменена!", "success")
    return redirect(url_for('main.profile'))


"""
Отображает список избранных сотрудников (для владельца) или проектов (для сотрудника).
"""
@main_bp.route('/favourite', methods=['GET', 'POST'])
@login_required
def favourite():
    count_notifications = None
    owner_exists = Owner.query.filter_by(user_id=current_user.id).first()
    employee_exists = Employee.query.filter_by(user_id=current_user.id).first()

    if owner_exists:
        count_notifications = (
            db.session.query(func.count(Invite.id))
            .join(Project, Project.id == Invite.project_id)
            .join(StatusInvite, StatusInvite.id == Invite.status_id)
            .filter(Project.owner_id == owner_exists.id)
            .filter(StatusInvite.label == "Отправлен")
            .scalar()
        )
        if count_notifications > 100:
            count_notifications = "99+"

        employees = (db.session.query(Employee).join(Favourite_employees, Employee.id == Favourite_employees.employee_id)
            .filter(Favourite_employees.owner_id == owner_exists.id).all())

        for emp in employees:
            emp.fav = True

        return render_template('favourite.html', count_notifications=count_notifications, owner=True, employees=employees)
    elif employee_exists:
        count_notifications = (
            db.session.query(func.count(Invite.id))
            .join(StatusInvite, StatusInvite.id == Invite.status_id)
            .filter(Invite.employee_id == employee_exists.id)
            .filter(StatusInvite.label == "Отправлен")
            .scalar(
        ))
        if count_notifications > 100:
            count_notifications = "99+"
        projects = (
            db.session.query(Project)
            .join(Favourite_projects, Project.id == Favourite_projects.project_id)
            .filter(Favourite_projects.employee_id == employee_exists.id)
            .all()
        )

        for project in projects:
            project.fav = True
            project_roles = ProjectRoles.query.filter_by(project_id=project.id).all()
            role_labels = [RoleType.query.get(role.role_id).label for role in project_roles]
            project.roles_str = ', '.join(role_labels)

            project_employees = ProjectEmployee.query.filter_by(project_id=project.id).all()
            employees_info = []
            for pe in project_employees:
                employee = Employee.query.get(pe.employee_id)
                if employee:
                    full_name = f"{employee.name} {employee.surname}".strip()
                    employees_info.append((employee.id, full_name))

            project.employees = employees_info 

        return render_template('favourite.html', count_notifications=count_notifications, owner=False, projects=projects)
    else:
        pass


"""
Показывает уведомления о новых откликах и приглашениях. Поддерживает оба типа пользователей.
"""
@main_bp.route('/notifications', methods=['GET', 'POST'])
@login_required
def notifications():
    count_notifications = None
    owner_exists = Owner.query.filter_by(user_id=current_user.id).first()
    employee_exists = Employee.query.filter_by(user_id=current_user.id).first()
    owner = False
    employees = None

    if owner_exists:
        count_notifications = (
            db.session.query(func.count(Invite.id))
            .join(Project, Project.id == Invite.project_id)
            .join(StatusInvite, StatusInvite.id == Invite.status_id)
            .filter(Project.owner_id == owner_exists.id)
            .filter(StatusInvite.label == "Отправлен")
            .scalar()
        )
        if count_notifications > 100:
            count_notifications = "99+"

        owner = True
        projects = Project.query.filter_by(owner_id=owner_exists.id).all()

        favourites = Favourite_employees.query.filter_by(owner_id=owner_exists.id).all()
        fav_ids = {fav.employee_id for fav in favourites}

        for proj in projects:
            invite_links = (
                db.session.query(Employee, Invite)
                .join(Invite, Invite.employee_id == Employee.id)
                .filter(Invite.project_id == proj.id)
                .all()
            )
            employees_with_invite = []
            for emp, invite in invite_links:
                employees_with_invite.append({
                    "id": emp.id,
                    "name": emp.name,
                    "surname": emp.surname,
                    "about": emp.about,
                    "role": emp.role,
                    "involvement": emp.involvement,
                    "experience": emp.experience,
                    "target": emp.target,
                    "scope": emp.scope,
                    "conditions": emp.conditions,
                    "invite": invite,
                    "fav": emp.id in fav_ids
                })

            proj.employees_list = employees_with_invite

            project_employees = ProjectEmployee.query.filter_by(project_id=proj.id).all()
            participants = []
            for pe in project_employees:
                employee = Employee.query.get(pe.employee_id)
                if employee:
                    full_name = f"{employee.name} {employee.surname}".strip()
                    participants.append((employee.id, full_name))

            proj.employees = participants

    elif employee_exists:
        count_notifications = (
            db.session.query(func.count(Invite.id))
            .join(StatusInvite, StatusInvite.id == Invite.status_id)
            .filter(Invite.employee_id == employee_exists.id)
            .filter(StatusInvite.label == "Отправлен")
            .scalar(
        ))
        if count_notifications > 100:
            count_notifications = "99+"
        invites = Invite.query.filter_by(employee_id=employee_exists.id).all()
        project_ids = [invite.project_id for invite in invites]
        invite_dict = {invite.project_id: invite for invite in invites}

        projects = Project.query.filter(Project.id.in_(project_ids)).all()
        fav_projects = Favourite_projects.query.filter_by(employee_id=employee_exists.id).all()
        fav_project_ids = {fp.project_id for fp in fav_projects}

        for project in projects:
            project.fav = project.id in fav_project_ids
            project.invite = invite_dict.get(project.id)  # ✅ добавляем invite в проект

            project_employees = ProjectEmployee.query.filter_by(project_id=project.id).all()
            participants = []
            for pe in project_employees:
                emp = Employee.query.get(pe.employee_id)
                if emp:
                    full_name = f"{emp.name} {emp.surname}".strip()
                    participants.append((emp.id, full_name))
            project.employees = participants
    else:
        flash("Отказано в доступе", "error")
        return redirect(url_for('main.general'))

    return render_template(
        'notifications.html',
        count_notifications=count_notifications,
        owner=owner,
        projects=projects,
        employees=employees
    )


"""
Позволяет владельцу отправить приглашение сотруднику на участие в проекте.
"""
@main_bp.route('/add_invite', methods=['GET'])
@login_required
def add_invite():
    emp_id = request.args.get('emp_id')
    project_id = request.args.get('project_id')

    if not emp_id or not project_id:
        flash("Недостаточно данных для отправки приглашения", "error")
        return redirect(url_for('main.general'))

    owner = Owner.query.filter_by(user_id=current_user.id).first()
    project = Project.query.get(project_id)

    if not owner or not project or project.owner_id != owner.id:
        flash("Отказано в доступе", "error")
        return redirect(url_for('main.general'))

    existing_invite = Invite.query.filter_by(project_id=project.id, employee_id=emp_id).first()
    if existing_invite:
        flash("Приглашение уже отправлено", "info")
        return redirect(url_for('main.project', id=project_id))

    status = StatusInvite.query.filter_by(label="Отправлен").first()
    if not status:
        flash("Статус 'Отправлен' не найден", "error")
        return redirect(url_for('main.general'))

    invite = Invite(
        project_id=project.id,
        employee_id=emp_id,
        status_id=status.id
    )

    db.session.add(invite)
    db.session.commit()

    flash("Приглашение отправлено", "success")
    return redirect(url_for('main.project', id=project_id))


"""
Позволяет владельцу удалить ранее отправленное приглашение в проект.
"""
@main_bp.route('/remove_invite', methods=['GET'])
@login_required
def remove_invite():
    invite_id = request.args.get('invite_id')

    if not invite_id:
        flash("Не указан идентификатор приглашения", "error")
        return redirect(url_for('main.general'))

    invite = Invite.query.get(invite_id)
    if not invite:
        flash("Приглашение не найдено", "error")
        return redirect(url_for('main.general'))

    project = Project.query.filter_by(id=invite.project_id).first()
    owner = Owner.query.filter_by(user_id=current_user.id).first()
    if not owner or project.owner_id != owner.id:
        flash("Недостаточно прав для удаления", "error")
        return redirect(url_for('main.general'))

    db.session.delete(invite)
    db.session.commit()

    flash("Приглашение успешно удалено", "success")
    return redirect(url_for('main.project', id=invite.project_id))


"""
Позволяет сотруднику или владельцу принять приглашение на участие в проекте.
"""
@main_bp.route('/ok_invite', methods=['GET'])
@login_required
def ok_invite():
    invite_id = request.args.get('invite_id')

    if not invite_id:
        flash("Не указан идентификатор приглашения", "error")
        return redirect(url_for('main.general'))

    invite = Invite.query.get(invite_id)
    if not invite:
        flash("Приглашение не найдено", "error")
        return redirect(url_for('main.general'))


    project = Project.query.filter_by(id=invite.project_id).first()
    curent_owner = Owner.query.filter_by(user_id=current_user.id).first()
    if curent_owner:
        if not curent_owner or project.owner_id != curent_owner.id:
            flash("Недостаточно прав", "error")
            return redirect(url_for('main.general'))

    curent_employee = Employee.query.filter_by(user_id=current_user.id).first()
    if curent_employee:
        if not curent_employee or invite.employee_id != curent_employee.id:
            flash("Недостаточно прав", "error")
            return redirect(url_for('main.general'))

    status_accepted = StatusInvite.query.filter_by(label="Принят").first()
    if not status_accepted:
        flash("Статус 'Принят' не найден", "error")
        return redirect(url_for('main.general'))

    invite.status_id = status_accepted.id
    invite.status = status_accepted

    if ProjectEmployee.query.filter_by(project_id=invite.project_id, employee_id=invite.employee_id).first():
        flash("Участник уже в проекте", "error")
        return redirect(url_for('main.general'))
    projectEmp = ProjectEmployee(project_id=invite.project_id, employee_id=invite.employee_id)
    db.session.add(projectEmp)
    db.session.commit()

    flash("Приглашение принято", "success")
    return redirect(url_for('main.project', id=invite.project_id))


"""
Позволяет сотруднику или владельцу отклонить приглашение на участие в проекте.
"""
@main_bp.route('/no_invite', methods=['GET'])
@login_required
def no_invite():
    invite_id = request.args.get('invite_id')

    if not invite_id:
        flash("Не указан идентификатор приглашения", "error")
        return redirect(url_for('main.general'))

    invite = Invite.query.get(invite_id)
    if not invite:
        flash("Приглашение не найдено", "error")
        return redirect(url_for('main.general'))

    project = Project.query.filter_by(id=invite.project_id).first()
    curent_owner = Owner.query.filter_by(user_id=current_user.id).first()
    if curent_owner:
        if not curent_owner or project.owner_id != curent_owner.id:
            flash("Недостаточно прав", "error")
            return redirect(url_for('main.general'))

    curent_employee = Employee.query.filter_by(user_id=current_user.id).first()
    if curent_employee:
        if not curent_employee or invite.employee_id != curent_employee.id:
            flash("Недостаточно прав", "error")
            return redirect(url_for('main.general'))

    status_rejected = StatusInvite.query.filter_by(label="Отклонён").first()
    if not status_rejected:
        flash("Статус 'Отклонён' не найден", "error")
        return redirect(url_for('main.general'))

    invite.status_id = status_rejected.id
    invite.status = status_rejected
    db.session.commit()

    flash("Приглашение отклонено", "info")
    return redirect(url_for('main.project', id=invite.project_id))


"""
Фильтрует сотрудников по заданным параметрам и возвращает HTML с карточками результатов.
"""
@main_bp.route('/get_employees', methods=['POST'])
@login_required
def get_employees():
    filters = request.get_json()
    query = Employee.query

    if filters.get('role_id'):
        query = query.filter_by(role_id=filters['role_id'])
    if filters.get('scope_id'):
        query = query.filter_by(scope_id=filters['scope_id'])
    if filters.get('experience_id'):
        query = query.filter_by(experience_id=filters['experience_id'])
    if filters.get('involvement_id'):
        query = query.filter_by(involvement_id=filters['involvement_id'])
    if filters.get('conditions_id'):
        query = query.filter_by(conditions_id=filters['conditions_id'])
    if filters.get('target_id'):
        query = query.filter_by(target_id=filters['target_id'])

    if filters.get('text-search'):
        text = filters['text-search'].lower()
        query = (
            query
            .outerjoin(RoleType, Employee.role_id == RoleType.id)
            .outerjoin(ExperienceLevel, Employee.experience_id == ExperienceLevel.id)
            .outerjoin(TargetType, Employee.target_id == TargetType.id)
            .outerjoin(ProjectScopeType, Employee.scope_id == ProjectScopeType.id)
            .outerjoin(ConditionType, Employee.conditions_id == ConditionType.id)
            .outerjoin(InvolvementType, Employee.involvement_id == InvolvementType.id)
            .filter(
                db.or_(
                    Employee.name.ilike(f"%{text}%"),
                    Employee.surname.ilike(f"%{text}%"),
                    Employee.about.ilike(f"%{text}%"),
                    RoleType.label.ilike(f"%{text}%"),
                    ExperienceLevel.label.ilike(f"%{text}%"),
                    TargetType.label.ilike(f"%{text}%"),
                    ProjectScopeType.label.ilike(f"%{text}%"),
                    ConditionType.label.ilike(f"%{text}%"),
                    InvolvementType.label.ilike(f"%{text}%")
                )
            )
        )

    employees = query.all()

    owner_exists = Owner.query.filter_by(user_id=current_user.id).first()
    favourites = Favourite_employees.query.filter_by(owner_id=owner_exists.id).all()
    fav_ids = {fav.employee_id for fav in favourites}

    for emp in employees:
        emp.fav = emp.id in fav_ids

    return render_template("partials/employees_cards.html", employees=employees, owner=True)

"""
Фильтрует проекты по параметрам (сфера, этап, условия, цель, роль и текст) и возвращает HTML.
"""
@main_bp.route('/get_project', methods=['POST'])
@login_required
def get_project():
    filters = request.get_json()
    query = Project.query

    if 'role_id' in filters:
        query = query.join(ProjectRoles).filter(ProjectRoles.role_id == filters['role_id'])
    if 'scope_id' in filters:
        query = query.filter(Project.scope_id == filters['scope_id'])
    if 'stage_id' in filters:
        query = query.filter(Project.stage_id == filters['stage_id'])
    if 'conditions_id' in filters:
        query = query.filter(Project.conditions_id == filters['conditions_id'])
    if 'target_id' in filters:
        query = query.filter(Project.target_id == filters['target_id'])

    if 'text-search' in filters:
        text = filters['text-search'].lower()
        query = (
            query
            .outerjoin(ProjectScopeType, Project.scope_id == ProjectScopeType.id)
            .outerjoin(ProjectStageType, Project.stage_id == ProjectStageType.id)
            .outerjoin(ProjectTargetType, Project.target_id == ProjectTargetType.id)
            .outerjoin(ProjectConditionsType, Project.conditions_id == ProjectConditionsType.id)
            .outerjoin(ProjectRoles, Project.id == ProjectRoles.project_id)
            .outerjoin(RoleType, ProjectRoles.role_id == RoleType.id)
            .filter(
                db.or_(
                    Project.title.ilike(f"%{text}%"),
                    Project.about.ilike(f"%{text}%"),
                    ProjectScopeType.label.ilike(f"%{text}%"),
                    ProjectStageType.label.ilike(f"%{text}%"),
                    ProjectTargetType.label.ilike(f"%{text}%"),
                    ProjectConditionsType.label.ilike(f"%{text}%"),
                    RoleType.label.ilike(f"%{text}%")
                )
            )
        )

    projects = query.all()

    employee_exists = Employee.query.filter_by(user_id=current_user.id).first()
    favourites = Favourite_projects.query.filter_by(employee_id=employee_exists.id).all()
    fav_project_ids = {fav.project_id for fav in favourites}

    for project in projects:
        project_roles = ProjectRoles.query.filter_by(project_id=project.id).all()
        role_labels = [RoleType.query.get(role.role_id).label for role in project_roles]
        project.roles_str = ', '.join(role_labels)

        project_employees = ProjectEmployee.query.filter_by(project_id=project.id).all()
        participants = []
        for pe in project_employees:
            employee = Employee.query.get(pe.employee_id)
            if employee:
                full_name = f"{employee.name} {employee.surname}".strip()
                participants.append((employee.id, full_name))
        project.employees = participants

        project.fav = project.id in fav_project_ids

    return render_template("partials/projects_cards.html", projects=projects, owner=False)