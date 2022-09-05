from wordlette.forms import Form
from wordlette.pages import Page


class LoginForm(Form):
    name: str
    password: str


class User:
    def __init__(self, name):
        self.name = name


class LoginFailedError(Exception):
    pass


class LoginPage(Page):
    path = "/login"

    async def response(self, user: User | None = None):
        if not user:
            return """<form method="post">
                Name: <input name="name" /><br />
                Password: <input name="password" type="password" /><br />
                <button>Login</button>
            </form>
            <p>The username is <code>Admin</code> and the password is <code>password</code>."""

        return f"Welcome {user.name}<br /><a href='/login'>Login Again</a>"

    async def on_login_submit(self, form: LoginForm) -> User:
        if form.password != "password" or form.name != "Admin":
            raise LoginFailedError("Your username or password was incorrect")

        return User(form.name)

    async def on_login_error(self, error: LoginFailedError):
        return f"There was a problem: {error.args[0]}<br /><a href='/login'>Login Again</a>"
