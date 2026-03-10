def is_field_agent(user):
    """Default field agent check: any authenticated active user."""
    return user.is_authenticated and user.is_active


def get_user_admin_unit(user):
    """Default admin unit getter: returns None."""
    return None
