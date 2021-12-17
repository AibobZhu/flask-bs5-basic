# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, flash, Markup, Blueprint, current_app, url_for
import warnings

try:  # pragma: no cover
    from wtforms.fields import HiddenField
except ImportError:
    def is_hidden_field_filter(field):
        raise RuntimeError('WTForms is not installed.')
else:
    def is_hidden_field_filter(field):
        return isinstance(field, HiddenField)

CDN_BASE = 'https://cdn.jsdelivr.net/npm'

from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField, BooleanField, PasswordField, IntegerField,\
    FormField, SelectField, FieldList
from wtforms.validators import DataRequired, Length
from wtforms.fields import *

#from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy


def raise_helper(message):  # pragma: no cover
    raise RuntimeError(message)


def get_table_titles(data, primary_key, primary_key_title):
    """Detect and build the table titles tuple from ORM object, currently only support SQLAlchemy.

    .. versionadded:: 1.4.0
    """
    if not data:
        return []
    titles = []
    for k in data[0].__table__.columns.keys():
        if not k.startswith('_'):
            titles.append((k, k.replace('_', ' ').title()))
    titles[0] = (primary_key, primary_key_title)
    return titles


class _Bootstrap:
    """
    Base extension class for different Bootstrap versions.

    .. versionadded:: 2.0.0
    """

    bootstrap_version = None
    jquery_version = None
    popper_version = None
    bootstrap_css_integrity = None
    bootstrap_js_integrity = None
    jquery_integrity = None
    popper_integrity = None
    static_folder = None
    bootstrap_css_filename = 'bootstrap.min.css'
    bootstrap_js_filename = 'bootstrap.min.js'
    jquery_filename = 'jquery.min.js'
    popper_filename = 'popper.min.js'

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['bootstrap'] = self

        blueprint = Blueprint('bootstrap', __name__, static_folder=f'static/{self.static_folder}',
                              static_url_path=f'/bootstrap{app.static_url_path}',
                              template_folder='templates')
        app.register_blueprint(blueprint)

        app.jinja_env.globals['bootstrap'] = self
        app.jinja_env.globals['bootstrap_is_hidden_field'] = is_hidden_field_filter
        app.jinja_env.globals['get_table_titles'] = get_table_titles
        app.jinja_env.globals['warn'] = warnings.warn
        app.jinja_env.globals['raise'] = raise_helper
        app.jinja_env.add_extension('jinja2.ext.do')
        # default settings
        app.config.setdefault('BOOTSTRAP_SERVE_LOCAL', False)
        app.config.setdefault('BOOTSTRAP_BTN_STYLE', 'primary')
        app.config.setdefault('BOOTSTRAP_BTN_SIZE', 'md')
        app.config.setdefault('BOOTSTRAP_BOOTSWATCH_THEME', None)
        app.config.setdefault('BOOTSTRAP_ICON_SIZE', '1em')
        app.config.setdefault('BOOTSTRAP_ICON_COLOR', None)
        app.config.setdefault('BOOTSTRAP_MSG_CATEGORY', 'primary')
        app.config.setdefault('BOOTSTRAP_TABLE_VIEW_TITLE', 'View')
        app.config.setdefault('BOOTSTRAP_TABLE_EDIT_TITLE', 'Edit')
        app.config.setdefault('BOOTSTRAP_TABLE_DELETE_TITLE', 'Delete')
        app.config.setdefault('BOOTSTRAP_TABLE_NEW_TITLE', 'New')

    def load_css(self, version=None, bootstrap_sri=None):
        """Load Bootstrap's css resources with given version.

        .. versionadded:: 0.1.0

        :param version: The version of Bootstrap.
        """
        serve_local = current_app.config['BOOTSTRAP_SERVE_LOCAL']
        bootswatch_theme = current_app.config['BOOTSTRAP_BOOTSWATCH_THEME']
        if version is None:
            version = self.bootstrap_version
        bootstrap_sri = self._get_sri('bootstrap_css', version, bootstrap_sri)

        if serve_local:
            if not bootswatch_theme:
                base_path = 'css'
            else:
                base_path = f'css/bootswatch/{bootswatch_theme.lower()}'
            boostrap_url = url_for('bootstrap.static', filename=f'{base_path}/{self.bootstrap_css_filename}')
        else:
            if not bootswatch_theme:
                base_path = f'{CDN_BASE}/bootstrap@{version}/dist/css'
            else:
                base_path = f'{CDN_BASE}/bootswatch@{version}/dist/{bootswatch_theme.lower()}'
            boostrap_url = f'{base_path}/{self.bootstrap_css_filename}'

        if bootstrap_sri and not bootswatch_theme:
            css = f'<link rel="stylesheet" href="{boostrap_url}" integrity="{bootstrap_sri}" crossorigin="anonymous">'
        else:
            css = f'<link rel="stylesheet" href="{boostrap_url}">'
        return Markup(css)

    def _get_js_script(self, version, name, sri):
        """Get <script> tag for JavaScipt resources."""
        serve_local = current_app.config['BOOTSTRAP_SERVE_LOCAL']
        paths = {
            'bootstrap': f'js/{self.bootstrap_js_filename}',
            'jquery': f'{self.jquery_filename}',
            '@popperjs/core': f'umd/{self.popper_filename}',
            'popper.js': f'umd/{self.popper_filename}',
        }
        if serve_local:
            url = url_for('bootstrap.static', filename=paths[name])
        else:
            url = f'{CDN_BASE}/{name}@{version}/dist/{paths[name]}'
        if sri:
            return f'<script src="{url}" integrity="{sri}" crossorigin="anonymous"></script>'
        return f'<script src="{url}"></script>'

    def _get_sri(self, name, version, sri):
        serve_local = current_app.config['BOOTSTRAP_SERVE_LOCAL']
        sris = {
            'bootstrap_css': self.bootstrap_css_integrity,
            'bootstrap_js': self.bootstrap_js_integrity,
            'jquery': self.jquery_integrity,
            'popper': self.popper_integrity,
        }
        versions = {
            'bootstrap_css': self.bootstrap_version,
            'bootstrap_js': self.bootstrap_version,
            'jquery': self.jquery_version,
            'popper': self.popper_version
        }
        if sri is not None:
            return sri
        if version == versions[name] and serve_local is False:
            return sris[name]
        return None

    def load_js(self, version=None, jquery_version=None,  # noqa: C901
                popper_version=None, with_jquery=True, with_popper=True,
                bootstrap_sri=None, jquery_sri=None, popper_sri=None):
        """Load Bootstrap and related library's js resources with given version.

        .. versionadded:: 0.1.0

        :param version: The version of Bootstrap.
        :param jquery_version: The version of jQuery (only needed with Bootstrap 4).
        :param popper_version: The version of Popper.js.
        :param with_jquery: Include jQuery or not (only needed with Bootstrap 4).
        :param with_popper: Include Popper.js or not.
        """
        if version is None:
            version = self.bootstrap_version
        if popper_version is None:
            popper_version = self.popper_version

        bootstrap_sri = self._get_sri('bootstrap_js', version, bootstrap_sri)
        popper_sri = self._get_sri('popper', popper_version, popper_sri)
        bootstrap = self._get_js_script(version, 'bootstrap', bootstrap_sri)
        popper = self._get_js_script(popper_version, self.popper_name, popper_sri) if with_popper else ''
        if version.startswith('4'):
            if jquery_version is None:
                jquery_version = self.jquery_version
            jquery_sri = self._get_sri('jquery', jquery_version, jquery_sri)
            jquery = self._get_js_script(jquery_version, 'jquery', jquery_sri) if with_jquery else ''
            return Markup(f'''{jquery}
        {popper}
        {bootstrap}''')
        return Markup(f'''{popper}
        {bootstrap}''')


class Bootstrap5(_Bootstrap):
    """
    Base class for Bootstrap 5.

    Initilize the extension::

        from flask import Flask
        from flask_bootstrap import Bootstrap5

        app = Flask(__name__)
        bootstrap = Bootstrap5(app)

    Or with the application factory::

        from flask import Flask
        from flask_bootstrap import Bootstrap5

        bootstrap = Bootstrap5()

        def create_app():
            app = Flask(__name__)
            bootstrap5.init_app(app)

    .. versionadded:: 2.0.0
    """
    bootstrap_version = '5.1.1'
    popper_version = '2.10.1'
    bootstrap_css_integrity = 'sha384-F3w7mX95PdgyTmZZMECAngseQB83DfGTowi0iMjiWaeVhAn4FJkqJByhZMI3AhiU'
    bootstrap_js_integrity = 'sha384-skAcpIdS7UcVUC05LJ9Dxay8AXcDYfBJqt1CJ85S/CFujBsIzCIv+l9liuYLaMQ/'
    popper_integrity = 'sha384-W8fXfP3gkOKtndU4JGtKDvXbO53Wy8SZCQHczT5FMiiqmQfUpWbYdTil/SxwZgAN'
    popper_name = '@popperjs/core'
    static_folder = 'bootstrap5'


app = Flask(__name__)
app.secret_key = 'dev'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

# set default button sytle and size, will be overwritten by macro parameters
app.config['BOOTSTRAP_BTN_STYLE'] = 'primary'
app.config['BOOTSTRAP_BTN_SIZE'] = 'sm'
# app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = 'lumen'  # uncomment this line to test bootswatch theme

# set default icon title of table actions
app.config['BOOTSTRAP_TABLE_VIEW_TITLE'] = 'Read'
app.config['BOOTSTRAP_TABLE_EDIT_TITLE'] = 'Update'
app.config['BOOTSTRAP_TABLE_DELETE_TITLE'] = 'Remove'
app.config['BOOTSTRAP_TABLE_NEW_TITLE'] = 'Create'

bootstrap = Bootstrap5(app)
db = SQLAlchemy(app)
csrf = CSRFProtect(app)


class ExampleForm(FlaskForm):
    """An example form that contains all the supported bootstrap style form fields."""
    date = DateField(description="We'll never share your email with anyone else.")  # add help text with `description`
    datetime = DateTimeField(render_kw={'placeholder': 'this is placeholder'})  # add HTML attribute with `render_kw`
    image = FileField(render_kw={'class': 'my-class'})  # add your class
    option = RadioField(choices=[('dog', 'Dog'), ('cat', 'Cat'), ('bird', 'Bird'), ('alien', 'Alien')])
    select = SelectField(choices=[('dog', 'Dog'), ('cat', 'Cat'), ('bird', 'Bird'), ('alien', 'Alien')])
    selectmulti = SelectMultipleField(choices=[('dog', 'Dog'), ('cat', 'Cat'), ('bird', 'Bird'), ('alien', 'Alien')])
    bio = TextAreaField()
    title = StringField()
    secret = PasswordField()
    remember = BooleanField('Remember me')
    submit = SubmitField()


class HelloForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(8, 150)])
    remember = BooleanField('Remember me')
    submit = SubmitField()


class ButtonForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 20)])
    submit = SubmitField()
    delete = SubmitField()
    cancel = SubmitField()


class TelephoneForm(FlaskForm):
    country_code = IntegerField('Country Code')
    area_code = IntegerField('Area Code/Exchange')
    number = StringField('Number')


class IMForm(FlaskForm):
    protocol = SelectField(choices=[('aim', 'AIM'), ('msn', 'MSN')])
    username = StringField()


class ContactForm(FlaskForm):
    first_name = StringField()
    last_name = StringField()
    mobile_phone = FormField(TelephoneForm)
    office_phone = FormField(TelephoneForm)
    emails = FieldList(StringField("Email"), min_entries=3)
    im_accounts = FieldList(FormField(IMForm), min_entries=2)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    draft = db.Column(db.Boolean, default=False, nullable=False)
    create_time = db.Column(db.Integer, nullable=False, unique=True)


@app.before_first_request
def before_first_request_func():
    db.drop_all()
    db.create_all()
    for i in range(20):
        m = Message(
            text=f'Test message {i+1}',
            author=f'Author {i+1}',
            category=f'Category {i+1}',
            create_time=4321*(i+1)
            )
        if i % 4:
            m.draft = True
        db.session.add(m)
    db.session.commit()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/form', methods=['GET', 'POST'])
def test_form():
    form = HelloForm()
    return render_template('form.html', form=form, telephone_form=TelephoneForm(), contact_form=ContactForm(), im_form=IMForm(), button_form=ButtonForm(), example_form=ExampleForm())


@app.route('/nav', methods=['GET', 'POST'])
def test_nav():
    return render_template('nav.html')


@app.route('/pagination', methods=['GET', 'POST'])
def test_pagination():
    page = request.args.get('page', 1, type=int)
    pagination = Message.query.paginate(page, per_page=10)
    messages = pagination.items
    return render_template('pagination.html', pagination=pagination, messages=messages)


@app.route('/flash', methods=['GET', 'POST'])
def test_flash():
    flash('A simple default alert—check it out!')
    flash('A simple primary alert—check it out!', 'primary')
    flash('A simple secondary alert—check it out!', 'secondary')
    flash('A simple success alert—check it out!', 'success')
    flash('A simple danger alert—check it out!', 'danger')
    flash('A simple warning alert—check it out!', 'warning')
    flash('A simple info alert—check it out!', 'info')
    flash('A simple light alert—check it out!', 'light')
    flash('A simple dark alert—check it out!', 'dark')
    flash(Markup('A simple success alert with <a href="#" class="alert-link">an example link</a>. Give it a click if you like.'), 'success')
    return render_template('flash.html')


@app.route('/table')
def test_table():
    page = request.args.get('page', 1, type=int)
    pagination = Message.query.paginate(page, per_page=10)
    messages = pagination.items
    titles = [('id', '#'), ('text', 'Message'), ('author', 'Author'), ('category', 'Category'), ('draft', 'Draft'), ('create_time', 'Create Time')]
    return render_template('table.html', messages=messages, titles=titles, Message=Message)


@app.route('/table/<int:message_id>/view')
def view_message(message_id):
    message = Message.query.get(message_id)
    if message:
        return f'Viewing {message_id} with text "{message.text}". Return to <a href="/table">table</a>.'
    return f'Could not view message {message_id} as it does not exist. Return to <a href="/table">table</a>.'


@app.route('/table/<int:message_id>/edit')
def edit_message(message_id):
    message = Message.query.get(message_id)
    if message:
        message.draft = not message.draft
        db.session.commit()
        return f'Message {message_id} has been editted by toggling draft status. Return to <a href="/table">table</a>.'
    return f'Message {message_id} did not exist and could therefore not be edited. Return to <a href="/table">table</a>.'


@app.route('/table/<int:message_id>/delete', methods=['POST'])
def delete_message(message_id):
    message = Message.query.get(message_id)
    if message:
        db.session.delete(message)
        db.session.commit()
        return f'Message {message_id} has been deleted. Return to <a href="/table">table</a>.'
    return f'Message {message_id} did not exist and could therefore not be deleted. Return to <a href="/table">table</a>.'


@app.route('/table/<int:message_id>/like')
def like_message(message_id):
    return f'Liked the message {message_id}. Return to <a href="/table">table</a>.'


@app.route('/table/new-message')
def new_message():
    return 'Here is the new message page. Return to <a href="/table">table</a>.'


@app.route('/icon')
def test_icon():
    return render_template('icon.html')


@app.route('/webbuilder')
def wb_builder():
    return render_template('web_builder.html')

if __name__ == '__main__':
    app.run(debug=True)
