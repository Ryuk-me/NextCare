import json
from typing import List
from app.database import SessionLocal
from app.models import user_model
from sqlalchemy.orm import Session
from app.scheams import user_schema, doctor_schema, clinic_schema, appointment_schema, admin_schema, change_password_schema
from passlib.hash import bcrypt
from app.models import user_model, doctor_model, clinic_model, appointment_model, admin_model
from app.error_handlers import errors
from datetime import date, datetime
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.Config import settings
import uuid
from pathlib import Path


def get_db():
    db = SessionLocal()
    create_first_admin(db)
    try:
        yield db
    finally:
        db.close()


# ***********************************************************************************
#                                                                                   #
#                              USER SERVICES                                        #
#                                                                                   #
# ***********************************************************************************


async def create_user(db: Session, user: user_schema.UserCreate, created_by_admin=False):
    if not is_user_exist(db, user.email):
        if not get_admin_by_email(db, user.email):
            if not is_doctor_exist(db, user.email):
                if not get_doctor_by_phone_no(db, user.phone):
                    if not get_user_by_phone_no(db, user.phone):
                        hash = hash_password(user.password)
                        temp_pass = user.password
                        user.password = hash
                        if created_by_admin:
                            user = user_model.User(
                                age=calculate_age(user.dob), is_active=True, **user.dict())
                        else:
                            user = user_model.User(
                                age=calculate_age(user.dob), **user.dict())
                        db.add(user)
                        db.commit()
                        db.refresh(user)
                        if(created_by_admin):
                            await send_welcome_email_admin(
                                subject=f"Welcome to FindCare {user.name} !",
                                recipients=user.email,
                                password=temp_pass,
                            )
                        return user
                raise errors.PHONE_NUMBER_ALREADY_EXIST
    raise errors.EMAIL_ALREADY_EXIST


def get_user(db: Session, id: str):
    return db.query(user_model.User).filter(
        user_model.User.id == id).first()


def is_user_exist(db: Session, email: str):
    user = db.query(user_model.User).filter(
        user_model.User.email == email).first()
    return user


def get_user_by_phone_no(db: Session, phone: str):
    user = db.query(user_model.User).filter(
        user_model.User.phone == phone).first()
    return user


# ***********************************************************************************
#                                                                                   #
#                             DOCTOR SERVICES                                       #
#                                                                                   #
# ***********************************************************************************


async def create_doctor(db: Session, doctor: doctor_schema.DoctorCreate, created_by_admin=False):
    if not is_doctor_exist(db, doctor.email):
        if not get_admin_by_email(db, doctor.email):
            if not is_user_exist(db, doctor.email):
                if not get_user_by_phone_no(db, doctor.phone):
                    if not get_doctor_by_phone_no(db, doctor.phone):
                        if not get_doctor_by_rgnum(db, doctor.registration_number):
                            age = calculate_age(doctor.dob)
                            if not doctor.experience_year < age - 18:
                                raise errors.NOT_POSSIBLE_EXPERINCE_YEAR
                            hash = hash_password(doctor.password)
                            temp_pass = doctor.password
                            doctor.password = hash
                            if created_by_admin:
                                doctor = doctor_model.Doctor(
                                    age=age, is_active=True, slug=generate_slug(doctor.name), **doctor.dict())
                            else:
                                doctor = doctor_model.Doctor(
                                    age=age, slug=generate_slug(doctor.name), **doctor.dict())
                            db.add(doctor)
                            db.commit()
                            db.refresh(doctor)
                            if(created_by_admin):
                                await send_welcome_email_admin(
                                    subject=f"Welcome to FindCare {doctor.name} !",
                                    recipients=doctor.email,
                                    password=temp_pass,
                                )
                            return doctor
                        raise errors.DOCTOR_WITH_THIS_REGISTRATION_NUM_ALREADY_EXIST
                raise errors.PHONE_NUMBER_ALREADY_EXIST
    raise errors.EMAIL_ALREADY_EXIST


def get_doctor(db: Session, id: str):
    return db.query(doctor_model.Doctor).filter(
        doctor_model.Doctor.id == id).first()


def is_doctor_exist(db: Session, email: str):
    doctor = db.query(doctor_model.Doctor).filter(
        doctor_model.Doctor.email == email).first()
    return doctor


def get_doctor_by_phone_no(db: Session, phone: str):
    doctor = db.query(doctor_model.Doctor).filter(
        doctor_model.Doctor.phone == phone).first()
    return doctor


def get_doctor_by_rgnum(db: Session, registration_number: str):
    doctor = db.query(doctor_model.Doctor).filter(
        doctor_model.Doctor.registration_number == registration_number).first()
    return doctor

# ***********************************************************************************
#                                                                                   #
#                            CLINIC SERVICES                                        #
#                                                                                   #
# ***********************************************************************************


def add_clinic(db: Session, clinic: clinic_schema.ClinicCreate, doctor_id: str):
    if not is_clinic_exist(db, clinic, doctor_id):
        clinic = clinic_model.Clinic(doctor_id=doctor_id, slots=calculate_slots(
            clinic.opens_at, clinic.closes_at, clinic.session_time), **clinic.dict())
        db.add(clinic)
        db.commit()
        db.refresh(clinic)
        return clinic
    raise errors.ALREADY_EXIST_CLINIC


def get_clinic(db: Session, doctor_id: str):
    clinic = db.query(clinic_model.Clinic).filter(
        clinic_model.Clinic.doctor_id == doctor_id).first()
    if clinic:
        return clinic
    raise errors.NOT_FOUND_ERROR


def is_clinic_exist(db: Session, clinic: clinic_schema.ClinicCreate, doctor_id: str):
    clinic = db.query(clinic_model.Clinic).filter(
        clinic_model.Clinic.doctor_id == doctor_id).first()
    return clinic


def is_clinic_exist_by_id(db: Session, clinic_id: str):
    clinic = db.query(clinic_model.Clinic).filter(
        clinic_model.Clinic.id == clinic_id).first()
    return clinic


# ***********************************************************************************
#                                                                                   #
#                        APPOINTMENT SERVICES                                       #
#                                                                                   #
# ***********************************************************************************


def add_appointment(db: Session, appointment: appointment_schema.CreateAppointment, user_id: str):
    clinic: clinic_schema.ClinicOut = is_clinic_exist_by_id(
        db, appointment.clinic_id)
    if clinic:
        if not clinic.doctor.is_verified:
            raise errors.DOCTOR_IS_NOT_VERIFIED
        if clinic.doctor.is_banned:
            raise errors.DOCTOR_IS_BANNED
        if clinic.is_open:
            appointment = appointment_model.Appointment(
                user_id=user_id, doctor_id=clinic.doctor_id, cid=clinic.id, **appointment.dict())
            db.add(appointment)
            db.commit()
            db.refresh(appointment)
            return appointment
        raise errors.CLINIC_IS_NOT_SERVICEABLE

    raise errors.CLINIC_NOT_FOUND


def cancel_appointments(db: Session, appointment: appointment_schema.AppointmentOutUser | appointment_schema.AppointmentOut, reason: str = None, is_User=False):
    appointment: appointment_schema.AppointmentOutUser | appointment_schema.AppointmentOut = db.query(appointment_model.Appointment).filter(
        appointment_model.Appointment.id == appointment.id).first()
    if appointment.is_completed:
        raise errors.APPOINTMENT_ALREADY_COMPLETED
    if is_User:
        if appointment.is_cancelled == 'U':
            raise errors.APPOINTNEMT_ALREADY_CANCELLED
        if appointment.is_cancelled == 'D':
            raise errors.APPOINTMENT_ALREADY_CANCELLED_BY_DR
        appointment.is_cancelled = 'U'
    else:
        if not reason:
            raise errors.NO_CANCELLATION_REASON
        if appointment.is_cancelled == 'U':
            raise errors.APPOINTNEMT_ALREADY_CANCELLED_BY_USER
        if appointment.is_cancelled == 'D':
            raise errors.APPOINTMENT_ALREADY_CANCELLED_BY_DR
        appointment.is_cancelled = 'D'
        appointment.cancellation_reason = reason
    appointment.when_cancelled = datetime.now()
    db.commit()
    return {"detail": "Appointment cancelled sucessfully"}


def appointment_completed(db: Session, appointment: appointment_schema.AppointmentOut):
    appointment: appointment_schema.AppointmentOut = db.query(appointment_model.Appointment).filter(
        appointment_model.Appointment.id == appointment.id).first()
    if appointment.is_completed:
        raise errors.APPOINTMENT_ALREADY_COMPLETED
    if appointment.is_cancelled == 'U':
        raise errors.APPOINTNEMT_ALREADY_CANCELLED_BY_USER
    if appointment.is_cancelled == 'D':
        raise errors.APPOINTMENT_ALREADY_CANCELLED_BY_DR
    appointment.is_completed = True
    db.commit()
    return {"detail": "Appointment completed sucessfully"}


def get_clinic_appointments(db: Session, doctor_id: str):
    appointments = db.query(appointment_model.Appointment).filter(
        appointment_model.Appointment.doctor_id == doctor_id).all()
    if appointments:
        return appointments
    raise errors.NO_APPOINTMENT_FOUND_ERROR


def get_all_appointment_by_user_id(db: Session, user_id: str):
    appointment = db.query(appointment_model.Appointment).filter(
        appointment_model.Appointment.user_id == user_id).all()
    if len(appointment) > 0:
        return appointment
    raise errors.NO_APPOINTMENT_FOUND_ERROR


def get_appointment_by_user_id(db: Session, id: str, user_id: str):
    appointment = db.query(appointment_model.Appointment).filter(
        appointment_model.Appointment.id == id, appointment_model.Appointment.user_id == user_id).first()
    if appointment:
        return appointment
    raise errors.NO_APPOINTMENT_FOUND_ERROR


def get_appointment_by_doctor_id(db: Session, id: str, doctor_id: str):
    appointment = db.query(appointment_model.Appointment).filter(
        appointment_model.Appointment.id == id, appointment_model.Appointment.doctor_id == doctor_id).first()
    if appointment:
        return appointment
    raise errors.NO_APPOINTMENT_FOUND_ERROR


# ***********************************************************************************
#                                                                                   #
#                              SEARCH CLINICS                                       #
#                                                                                   #
# ***********************************************************************************


def search_doctor_clinics(city: str, speciality: str | None, db: Session):
    if not speciality:
        clinic = db.query(clinic_model.Clinic).join(doctor_model.Doctor).filter(
            clinic_model.Clinic.address["city"].astext == city, doctor_model.Doctor.is_verified, doctor_model.Doctor.is_banned == False).all()
        if clinic:
            return clinic
        raise errors.NOT_FOUND_ERROR
    clinic = db.query(clinic_model.Clinic).join(doctor_model.Doctor).filter(
        clinic_model.Clinic.address["city"].astext == city, doctor_model.Doctor.speciality == speciality, doctor_model.Doctor.is_verified, doctor_model.Doctor.is_banned == False).all()
    if clinic:
        return clinic
    raise errors.NOT_FOUND_ERROR


# ***********************************************************************************
#                                                                                   #
#                             ADMIN SERVICES                                        #
#                                                                                   #
# ***********************************************************************************

def create_admin(db: Session, admin: admin_schema.CreateAdmin):
    if not is_admin_exist(db, admin.email):
        if not is_user_exist(db, admin.email):
            if not is_doctor_exist(db, admin.email):
                hash = hash_password(admin.password)
                admin.password = hash
                admin = admin_model.Admin(**admin.dict())
                db.add(admin)
                db.commit()
                db.refresh(admin)
                return admin
    raise errors.EMAIL_ALREADY_EXIST


def is_admin_exist(db: Session, email: str):
    admin = db.query(admin_model.Admin).filter(
        admin_model.Admin.email == email).first()
    return admin


def create_first_admin(db: Session):
    admin = is_admin_exist(db, settings.FIRST_SUPERUSER_EMAIL)
    if not admin:
        admin_in = admin_schema.CreateAdmin(
            email=settings.FIRST_SUPERUSER_EMAIL,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            name=settings.FIRST_SUPERUSER_NAME,
            is_super_admin=True
        )
        create_admin(db, admin_in)


def get_admin_me(db: Session, admin_id: str):
    admin = db.query(admin_model.Admin).filter(
        admin_model.Admin.id == admin_id).first()
    if admin:
        return admin
    raise errors.ACCOUNT_NOT_FOUND_WITH_THIS_EMAIL


def get_admin_by_email(db: Session, email: str):
    admin = db.query(admin_model.Admin).filter(
        admin_model.Admin.email == email).first()
    return admin


def get_all_clinics(db: Session):
    clinics = db.query(clinic_model.Clinic).all()
    if len(clinics) > 0:
        for clinic in clinics:
            clinic: clinic_schema.ClinicOutAdminPanel
            clinic_id = clinic.id
            appointments = db.query(appointment_model.Appointment).filter(
                appointment_model.Appointment.clinic_id == clinic_id).all()
            if len(appointments) > 0:
                total_appointments = len(appointments)
                completed_appointments = 0
                cancelled_appointments_by_doctor = 0
                cancelled_appointments_by_user = 0
                for appointment in appointments:
                    if appointment.is_completed:
                        completed_appointments += 1
                    if appointment.is_cancelled == "D":
                        cancelled_appointments_by_doctor += 1
                    if appointment.is_cancelled == "U":
                        cancelled_appointments_by_user += 1
                clinic.total_appointments = total_appointments
                clinic.completed_appointments = completed_appointments
                clinic.cancelled_appointments_by_user = cancelled_appointments_by_user
                clinic.cancelled_appointments_by_doctor = cancelled_appointments_by_doctor
                clinic.pending_appointments = total_appointments - \
                    (cancelled_appointments_by_user +
                     cancelled_appointments_by_doctor + completed_appointments)
        return clinics
    raise errors.CLINIC_NOT_FOUND


def verify_doctor(db: Session, doctor_id: str):
    doctor: doctor_schema.DoctorOut = db.query(doctor_model.Doctor).filter(
        doctor_model.Doctor.id == doctor_id).first()
    if doctor:
        if doctor.is_verified:
            raise errors.DOCTOR_IS_ALREADY_VERIFIED
        doctor.is_verified = True
        db.commit()
        return {"detail": "Doctor verified successfully"}
    raise errors.NO_DOCTOR_FOUND_WITH_THIS_ID


async def deactivate_account(db: Session, id: str, is_user: bool = False):
    if is_user:
        user: user_schema.UserOut = get_user(db, id)
        if not user:
            raise errors.USER_NOT_FOUND
        if not user.is_banned:
            user.is_banned = True
            user.when_banned = datetime.now()
            db.commit()
            await send_email_account_deactivation(
                subject="Account Deactivation", recipients=user.email)
            return {"detail": "User banned successfully"}
        raise errors.USER_ALREADY_BANNED
    else:
        doctor: doctor_schema.DoctorOut = get_doctor(db, id)
        if not doctor:
            raise errors.DOCTOR_NOT_FOUND
        if not doctor.is_banned:
            doctor.is_banned = True
            doctor.when_banned = datetime.now()
            db.commit()
            await send_email_account_deactivation(
                subject="Account Deactivation", recipients=user.email)
            return {"detail": "Doctor banned successfully"}
        raise errors.DOCTOR_IS_ALREADY_BANNED


async def activate_account(db: Session, id: str, is_user: bool = False):
    if is_user:
        user: user_schema.UserOut = get_user(db, id)
        if not user:
            raise errors.USER_NOT_FOUND
        if user.is_banned:
            user.is_banned = False
            user.when_banned = None
            db.commit()
            await send_email_account_activation(
                subject="Account Activation", recipients=user.email)
            return {"detail": "User unbanned successfully"}
        raise errors.USER_ALREADY_UNBANNED
    else:
        doctor: doctor_schema.DoctorOut = get_doctor(db, id)
        if not doctor:
            raise errors.DOCTOR_NOT_FOUND
        if doctor.is_banned:
            doctor.is_banned = False
            doctor.when_banned = None
            db.commit()
            await send_email_account_activation(
                subject="Account Activation", recipients=user.email)
            return {"detail": "Doctor unbanned successfully"}
        raise errors.DOCTOR_IS_ALREADY_UNBANNED


def get_all_users(db: Session):
    users = db.query(user_model.User).all()
    if len(users) > 0:
        for user in users:
            user: user_schema.UserOutAdminPanel
            user_id = user.id
            appointments = db.query(appointment_model.Appointment).filter(
                appointment_model.Appointment.user_id == user_id).all()
            if len(appointments) > 0:
                total_appointments = len(appointments)
                completed_appointments = 0
                cancelled_appointments_by_doctor = 0
                cancelled_appointments_by_user = 0
                for appointment in appointments:
                    if appointment.is_completed:
                        completed_appointments += 1
                    if appointment.is_cancelled == "D":
                        cancelled_appointments_by_doctor += 1
                    if appointment.is_cancelled == "U":
                        cancelled_appointments_by_user += 1
                user.total_appointments = total_appointments
                user.completed_appointments = completed_appointments
                user.cancelled_appointments_by_user = cancelled_appointments_by_user
                user.cancelled_appointments_by_doctor = cancelled_appointments_by_doctor
                user.pending_appointments = total_appointments - \
                    (cancelled_appointments_by_user +
                     cancelled_appointments_by_doctor + completed_appointments)
        return users
    raise errors.NO_USER_FOUND


# ***********************************************************************************
#                                                                                   #
#                         PASSWORD SERVICES                                         #
#                                                                                   #
# ***********************************************************************************


def change_password(db: Session, password: str, obj: change_password_schema.ChangePassword, current_db_obj=None):
    if verify_hash(password, obj.password):
        raise errors.PASSWORD_CANNOT_BE_SAME
    hash = hash_password(password)
    obj.password = hash
    if(current_db_obj):
        current_db_obj.updated_at = datetime.now()
    db.commit()
    return {"detail": "Password changed successfully"}


async def reset_password(db: Session, email: str):
    user = db.query(user_model.User).filter(
        user_model.User.email == email).first()
    doctor = db.query(doctor_model.Doctor).filter(
        doctor_model.Doctor.email == email).first()
    admin = db.query(admin_model.Admin).filter(
        admin_model.Admin.email == email).first()
    if not user or doctor or admin:
        raise errors.ACCOUNT_NOT_FOUND_WITH_THIS_EMAIL

    temp_gen_pass = generate_random_password()
    final_obj = None
    if user:
        final_obj = user
    if doctor:
        final_obj = doctor
    if admin:
        final_obj = admin
    change_password(db, temp_gen_pass, final_obj, final_obj)
    return await send_reset_password_mail(
        subject="Reset Password", recipients=final_obj.email, password=temp_gen_pass)


def generate_random_password():
    password = uuid.uuid4().hex.upper()[0:6]
    return password

# ***********************************************************************************
#                                                                                   #
#                               HASHING                                             #
#                                                                                   #
# ***********************************************************************************


def hash_password(password: str):
    return bcrypt.hash(password)


def verify_hash(password, hash):
    return bcrypt.verify(password, hash)


# ***********************************************************************************
#                                                                                   #
#                       UTILITY FUNCTIONS                                           #
#                                                                                   #
# ***********************************************************************************


def calculate_age(birthDate):
    today = date.today()
    age = today.year - birthDate.year - \
        ((today.month, today.day) < (birthDate.month, birthDate.day))

    return age


def generate_slug(full_name: str):
    full_name = full_name.lower().split()
    full_name[0] = full_name[0].replace('.', '')
    rnd_uuid = str(uuid.uuid4())
    slug = '-'.join(full_name) + "-" + str(rnd_uuid)
    return slug


def calculate_slots(opens_at, closes_at, session_time):
    FMT = '%H:%M:%S'
    t = str(datetime.strptime(str(closes_at), FMT) -
            datetime.strptime(str(opens_at), FMT)).split(':')
    total_minutes = int(int(t[0])*60+int(t[1])*1 + int(t[2])/60)
    slots = total_minutes // int(session_time)
    return slots


# ***********************************************************************************
#                                                                                   #
#                       EMAIL FUNCTIONS                                             #
#                                                                                   #
# ***********************************************************************************


async def send_welcome_email(subject: str, recipients: str, token_url: str):
    message = MessageSchema(
        subject=subject,
        recipients=[recipients],
        template_body={
            "token_url": token_url
        }
    )

    conf = login_mail()
    fm = FastMail(conf)
    await fm.send_message(message, template_name='new-user.html')

    return {"detail": "We have sent a verification link on your mail please verify to continue"}


async def send_welcome_email_admin(subject: str, recipients: str, password: str):
    message = MessageSchema(
        subject=subject,
        recipients=[recipients],
        template_body={
            "password": password
        }
    )
    conf = login_mail()
    fm = FastMail(conf)
    await fm.send_message(message, template_name='new-user-admin.html')


async def send_reset_password_mail(subject: str, recipients: str, password: str):
    message = MessageSchema(
        subject=subject,
        recipients=[recipients],
        template_body={
            "password": password
        }
    )
    conf = login_mail()
    fm = FastMail(conf)
    await fm.send_message(message, template_name='reset.html')
    return {"detail": "We have sent a temporary password on your mail."}


async def send_email_account_activation(subject: str, recipients: str):
    message = MessageSchema(
        subject=subject,
        recipients=[recipients],
        template_body={
            "just_a_place_holder": "just_a_place_holder"
        }
    )
    conf = login_mail()
    fm = FastMail(conf)
    await fm.send_message(message, template_name='account-reactivated.html')
    return {"detail": "Account Unblocked Successfully"}


async def send_email_account_deactivation(subject: str, recipients: str):
    message = MessageSchema(
        subject=subject,
        recipients=[recipients],
        template_body={
            "just_a_place_holder": "just_a_place_holder"
        }
    )
    conf = login_mail()
    fm = FastMail(conf)
    await fm.send_message(message, template_name='account-blocked.html')
    return {"detail": "Account Blocked Successfully"}


async def send_email_change(subject: str, recipients: str, token_url: str):
    message = MessageSchema(
        subject=subject,
        recipients=[recipients],
        template_body={
            "token_url": token_url
        }
    )
    conf = login_mail()
    fm = FastMail(conf)
    await fm.send_message(message, template_name='mail-change.html')
    return {"detail": "Email changed successfully please verify to continue"}


def login_mail():
    config = ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_TLS=True,
        MAIL_SSL=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
        TEMPLATE_FOLDER=Path(__file__).parent / 'email-templates',
    )
    return config
