class User:
    def __init__(
        self, 
        id: int = None, 
        first_name: str = "", 
        last_name: str = "", 
        phone: str = "", 
        email: str = "", 
        password: str = ""
    ):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.email = email
        self.password = password

    def to_dict(self):
        """Converts the model instance to a dictionary (for sending to Supabase)."""
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "email": self.email,
            "password": self.password
        }
