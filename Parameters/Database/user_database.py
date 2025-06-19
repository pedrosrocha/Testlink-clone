class DatabaseConnector:
    users = [
        {
            "id": 1,
            "username": "john",
            "password_hash": "$2b$12$QiinFQ2FIZDEX1CJgGEkaulWGuoHzlSYBWvp/2zZWoHpAppBZBUw6",
            "email": "pedro.vic13133@gmail.com"
        },
        {
            "id": 2,
            "username": "pedro",
            "password_hash": "$2a$12$y5wWahHx1uYjujhhNIeGkOVqiOCAYESa8rncXzNfgs3eKM0pv3/gu",
            "email": "pedro.vic13133@gmail.com"
        }
    ]

    @classmethod
    def return_all_users(self):
        return self.users

    @classmethod
    def add_user(self, username, encrypted_password, email):
        self.users.append({
            "id": self.return_next_id(),
            "username": username,
            "password_hash": encrypted_password,
            "email": email
        })

    @classmethod
    def return_next_id(self):
        # returns the last added id and then sums 1. This is used to insert a unique id to the dictionary/database.
        # If the list is empty, 1 will be returned
        if self.users:
            return self.users[-1]["id"] + 1
        return 1

    @classmethod
    def delete_user_from_database(self, user_id):
        New_users = [
            user for user in self.users if user["id"] != user_id
        ]
        self.users = New_users

    @classmethod
    def return_user_info(self, username):
        for user in self.users:
            if user["username"] == username:
                return user

        return None

    @classmethod
    def get_by_id(self, id):
        for user in self.users:
            if user["id"] == id:
                return user

        return None

    @classmethod
    def change_user_password(self, username, passoword_hash):
        for i in range(len(self.users)):
            if self.users[i]["username"] == username:
                self.users[i]["password_hash"] = passoword_hash
