class Manager:

    def __init__(self):

        self.allowedLetters = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890"
        self.phoneNumberAllowedLetters = "1234567890+ "

    def check_spelling(self, text, email=False, phone_number=False):

        accurate = True

        if text == "":
            accurate = False

        if not phone_number:
            for letter in text:
                if not letter in self.allowedLetters:
                    if email:
                        if letter == "@" or letter == ".":
                            continue
                    accurate = False
        else:
            for letter in text:
                if not letter in self.phoneNumberAllowedLetters:
                    accurate = False

        if email:
            if not "@" in text:
                accurate = False

        return accurate
