from flask import render_template, session, redirect, url_for

from . import user 
from app.user.user_form import LoginForm
from app.models import User


@user.route('/user/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user.password == form.password.data:
            return redirect(url_for('admin.index'))
        else:
            return redirect(url_for('main.index'))
    return render_template('user/login.html', form=form)
