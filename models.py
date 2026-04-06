from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
from datetime import datetime


db = SQLAlchemy()


def now_str() -> str:
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    nickname = db.Column(db.String(120), nullable=True)
    is_guest = db.Column(db.Boolean, nullable=False, default=True)
    membership_tier = db.Column(db.String(32), nullable=False, default='free')
    stripe_customer_id = db.Column(db.String(120), nullable=True, unique=True)
    created_at = db.Column(db.String(19), nullable=False, default=now_str)
    updated_at = db.Column(db.String(19), nullable=False, default=now_str)


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.String(19), nullable=False, default=now_str)
    user_group = db.Column(db.String(64), nullable=False)
    goal = db.Column(db.String(64), nullable=False)
    plan_scope = db.Column(db.String(16), nullable=False, default='week')
    cycle_length = db.Column(db.Integer, nullable=True)
    display_name = db.Column(db.String(120), nullable=True)
    sex = db.Column(db.String(32), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    height_cm = db.Column(db.Float, nullable=True)
    weight_kg = db.Column(db.Float, nullable=True)
    body_fat = db.Column(db.Float, nullable=True)
    activity_level = db.Column(db.String(64), nullable=True)
    level = db.Column(db.String(64), nullable=False)
    primary_stroke = db.Column(db.String(64), nullable=True)
    event_focus = db.Column(db.String(64), nullable=True)
    sessions_per_week = db.Column(db.Integer, nullable=False, default=3)
    session_duration = db.Column(db.Integer, nullable=False, default=45)
    discomfort = db.Column(db.String(255), nullable=False, default='没有明显不适')
    recent_result_flag = db.Column(db.String(32), nullable=False, default='无')
    best_result_distance = db.Column(db.String(64), nullable=True)
    best_result_time = db.Column(db.String(64), nullable=True)
    css_400 = db.Column(db.String(64), nullable=True)
    css_200 = db.Column(db.String(64), nullable=True)
    css_pace_seconds = db.Column(db.Float, nullable=True)
    watch_data_flag = db.Column(db.String(32), nullable=False, default='无')
    extra_note = db.Column(db.Text, nullable=True)


class TrainingPlan(db.Model):
    __tablename__ = 'training_plans'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profiles.id'), nullable=False)
    created_at = db.Column(db.String(19), nullable=False, default=now_str)
    plan_scope = db.Column(db.String(16), nullable=False, default='week')
    cycle_length = db.Column(db.Integer, nullable=True)
    plan_version = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(16), nullable=False, default='active', index=True)
    summary = db.Column(db.Text, nullable=False)
    data_json = db.Column(db.Text, nullable=False)
    calories_json = db.Column(db.Text, nullable=True)
    nutrition_json = db.Column(db.Text, nullable=True)


class TrainingFeedback(db.Model):
    __tablename__ = 'training_feedbacks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profiles.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('training_plans.id'), nullable=False, index=True)
    created_at = db.Column(db.String(19), nullable=False, default=now_str)
    session_index = db.Column(db.Integer, nullable=False, default=0)
    completion_status = db.Column(db.String(64), nullable=False)
    completion_ratio = db.Column(db.Float, nullable=True)
    fatigue_score = db.Column(db.Integer, nullable=False)
    discomfort_feedback = db.Column(db.String(64), nullable=False)
    sleep_status = db.Column(db.String(64), nullable=False)
    screenshot_storage_key = db.Column(db.String(255), nullable=True)
    screenshot_url = db.Column(db.String(500), nullable=True)
    screenshot_metrics_json = db.Column(db.Text, nullable=True)
    feedback_note = db.Column(db.Text, nullable=True)
    result_json = db.Column(db.Text, nullable=True)


class ExportLog(db.Model):
    __tablename__ = 'exports'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('training_plans.id'), nullable=False, index=True)
    created_at = db.Column(db.String(19), nullable=False, default=now_str)
    export_type = db.Column(db.String(16), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    storage_key = db.Column(db.String(255), nullable=True)
    storage_url = db.Column(db.String(500), nullable=True)


class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    provider = db.Column(db.String(32), nullable=False, default='stripe')
    stripe_customer_id = db.Column(db.String(120), nullable=True, index=True)
    stripe_subscription_id = db.Column(db.String(120), nullable=True, unique=True, index=True)
    stripe_price_id = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(32), nullable=False, default='inactive', index=True)
    current_period_end = db.Column(db.String(19), nullable=True)
    cancel_at_period_end = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.String(19), nullable=False, default=now_str)
    updated_at = db.Column(db.String(19), nullable=False, default=now_str)


class WebhookEvent(db.Model):
    __tablename__ = 'webhook_events'
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(32), nullable=False)
    event_id = db.Column(db.String(120), nullable=False)
    event_type = db.Column(db.String(120), nullable=False)
    processed_at = db.Column(db.String(19), nullable=False, default=now_str)
    __table_args__ = (UniqueConstraint('provider', 'event_id', name='uq_webhook_provider_event'),)


class EntitlementGrant(db.Model):
    __tablename__ = 'entitlement_grants'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    feature_code = db.Column(db.String(64), nullable=False, index=True)
    source = db.Column(db.String(64), nullable=False, default='manual')
    expires_at = db.Column(db.String(19), nullable=True)
    is_enabled = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.String(19), nullable=False, default=now_str)
    __table_args__ = (UniqueConstraint('user_id', 'feature_code', 'source', name='uq_user_feature_source'),)
