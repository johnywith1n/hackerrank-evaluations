import logging
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import (
    current_user,
    login_required,
)

from server.datastore_models.appconfigs import AppConfig
from server.datastore_models.users import UserPermissions, User, USER_PERMS
from server.datastore_models.assignments import Assignment

admin_blueprint = Blueprint('admin', __name__)


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not UserPermissions.is_admin(current_user.perms):
            return abort(403)
        return fn(*args, **kwargs)

    wrapper.__name__ = fn.__name__
    return wrapper


@admin_blueprint.route("/admin")
@login_required
@admin_required
def admin_home():
    return render_template('admin.html')


@admin_blueprint.route("/admin/configs", methods=['GET'])
@login_required
@admin_required
def admin_configs():
    appconfigs_keys = AppConfig.get_all_appconfig_keys()
    return render_template('admin_configs.html',
                           appconfigs_keys=appconfigs_keys)


@admin_blueprint.route("/admin/configs", methods=['POST'])
@login_required
@admin_required
def admin_configs_update():
    config_key = request.form.get('config-key')
    config_value = request.form.get('config-value')

    if config_key not in AppConfig.get_all_appconfig_keys().keys():
        flash('Invalid config key', 'danger')
    else:
        AppConfig.upsert(config_key, config_value)
        flash('Config updated!', 'primary')
    return redirect(url_for('admin.admin_configs'))


@admin_blueprint.route("/admin/configs/<config_key>", methods=['GET'])
@login_required
@admin_required
def admin_configs_lookup(config_key):
    appconfig = AppConfig.get(config_key)
    if appconfig:
        return dict(key=config_key, value=appconfig.get(AppConfig.value))
    else:
        return dict(key=config_key, value=None)


@admin_blueprint.route("/admin/perms", methods=['GET'])
@login_required
@admin_required
def admin_perms():
    users = User.get_all_user_emails()
    return render_template('admin_perms.html', users=users, USER_PERMS=USER_PERMS)


@admin_blueprint.route("/admin/perms", methods=['POST'])
@login_required
@admin_required
def admin_perms_form():
    user_id = request.form.get('user-id')
    error = False
    if not user_id:
        flash('Missing user id', 'danger')
        error = True

    user = User.get(user_id)
    if not user:
        flash('Invalid user id', 'danger')
        error = True

    if error:
        return redirect(url_for('admin.admin_perms'))

    perm_prefix = 'form-perm-'
    len_prefix = len(perm_prefix)
    new_perms = []
    for key in request.form:
        if key.startswith(perm_prefix):
            perm_name = key[len_prefix:]
            if perm_name in USER_PERMS and request.form[key] == 'on':
                new_perms.append(perm_name)
    user[User.perms] = new_perms
    try:
        User.update(user)
        flash('User permissions updated!', 'primary')
    except Exception as e:
        logging.exception(e)
        flash('Unable to update user', 'danger')
    return redirect(url_for('admin.admin_perms'))


@admin_blueprint.route("/admin/perms/<user_id>")
@login_required
@admin_required
def admin_perms_user_lookup(user_id):
    user = User.get(user_id)
    if user:
        return dict(status='success', data=dict(id=user_id, email=user.get(User.email), perms=user.get(User.perms)))
    else:
        return dict(status='missing user')


@admin_blueprint.route("/admin/delete_all_assignments")
@login_required
@admin_required
def admin_delete_all_assignments():
    try:
        keys = Assignment.get_all_assignments_keys_only()
        Assignment.bulk_delete(keys)
        flash('Deleted all assignments', 'primary')
    except Exception as e:
        logging.exception(e)
        flash('Failed to delete all assignments', 'danger')
    return redirect(url_for('admin.admin_home'))

