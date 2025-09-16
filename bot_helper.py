from collections import UserDict
from datetime import datetime, date, timedelta
import re
import pickle


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return f"{e} error"
            
    return inner


def string_to_date(date_string):
    return datetime.strptime(date_string, "%d.%m.%Y").date()


def date_to_string(date):
    return date.strftime("%d.%m.%Y")


def prepare_user_list(records):
    prepared_list = []
    for record in records:
        prepared_list.append({"name": record["name"], "birthday": string_to_date(record["birthday"])})
    return prepared_list


def find_next_weekday(start_date, weekday):
    days_ahead = weekday - start_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return start_date + timedelta(days=days_ahead)


def adjust_for_weekend(birthday):
    if birthday.weekday() >= 5:
        return find_next_weekday(birthday, 0)
    return birthday


class WrongFormatOfField(Exception):
    def __init__(self, message="Wrong format of field"):
        self.message = message
        super().__init__(self.message)


class Field:
    def __init__(self, value):
        self.value = value


    def __str__(self):
        return str(self.value)


    def __eq__(self, other):
        if isinstance(other, Field):
            return self.value == other.value
        return False


class Name(Field):
    pass


class Phone(Field):
     def __init__(self, value):
        if len(value) == 10 and value.isdecimal():
            super().__init__(value)
        else:
             raise WrongFormatOfField("The phone number should contain 10 numeric characters")


class Birthday(Field):
     def __init__(self, value):
         try:
             if value != 'None':
                 pattern = r"\d{2}\.\d{2}\.\d{4}"
                 match = re.search(pattern, value)
                 if match:
                     birthday = string_to_date(match.group())
                 else:
                     raise ValueError
             else:
                 birthday = None
             super().__init__(birthday)
         except ValueError:
             raise ValueError("Invalid date format. Use DD.MM.YYYY")

     def __str__(self):
         if self.value:
            return date_to_string(self.value)
         else:
            return 'None'

class Record:
    def __init__(self, name, phones = None, birthday = None):
        self.name = Name(name)
        self.phones =[Phone(phone) for phone in phones] if phones else []
        self.birthday = Birthday(birthday) if birthday else None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        if phone in self.phones:
            self.phones.remove(phone)
        else:
            raise ValueError(f"Phone number {phone} not found")

    def edit_phone(self, old_number, new_number):
        phone  = self.find_phone(old_number)
        if not phone :
             raise ValueError(f"Phone number {phone} not found")
        self.add_phone(new_number)
        self.remove_phone(phone)

    def find_phone(self, number):
        return next((phone for phone in self.phones 
                     if phone == Phone(number)), None)


    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)
    
    def __str__(self):
        return f"Contact: {self.name}, tel.: {'; '.join(str(phone) for phone in self.phones)}, birthday: {self.birthday}"


class AddressBook(UserDict):
    def __init__(self):
        self.data = {}

    
    def add_record(self, record: Record):
        if not str(record.name) in self.data.keys():
            self.data[str(record.name)] = record
        else:
            raise ValueError("Record with this name already exists")
        
    def update_record(self, record:Record):
        if str(record.name) in self.data.keys():
            self.data[str(record.name)] = record
        else:
            raise ValueError(f"Record {record.name} not found")
        
    def find(self, name):
        if name in self.data.keys():
            return self.data[name]
        else:
             raise ValueError(f"Record {name} not found")
        
    
    def check_record(self, record):
        return record in self.data.keys()


    def delete(self, name):
        if name in self.data.keys():
            del self.data[name]
        else:  
            raise KeyError(f"Record {name} not found")


    def get_upcoming_birthdays(self, days=7):
        upcoming_birthdays = []
        today = date.today()

        for key, record in self.data.items():
            if record.birthday.value:
                birthday_this_year = record.birthday.value.replace(year=today.year)
                if birthday_this_year < today:
                    birthday_this_year = record.birthday.value.replace(year=today.year + 1)

                if 0 <= (birthday_this_year - today).days <= days:
                    birthday_this_year = adjust_for_weekend(birthday_this_year)
                    congratulation_date_str = date_to_string(birthday_this_year)
                    upcoming_birthdays.append({"name": key, "birthday": congratulation_date_str})
        return upcoming_birthdays


    def __str__(self):
        return [f"{value}" for key,value in self.data]


def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


@input_error
def parse_input(user_input):
    cmd, *args = user_input.split(" ")
    cmd = cmd.strip().lower()
    return cmd, *args


@input_error
def add_contact(args, contacts:AddressBook):
    name, phone = args
    if contacts.check_record(name):
        record = contacts.find(name)
        record.add_phone(phone)
        contacts.update_record(record)
        return "Contact updated"
    record = Record(name)
    record.add_phone(phone)
    contacts.add_record(record)
    return "Contact added."

@input_error
def change_contact(args, contacts:AddressBook):
    name, old_phone, new_phone = args
    record = contacts.find(name)
    record.edit_phone(old_phone, new_phone)
    contacts.update_record(record)
    return "Contact changed."


@input_error
def show_phone(args, contacts:AddressBook):
    name = args[0]
    record = contacts.find(name)
    return f"tel: {'; '.join(map(str, record.phones))}"


@input_error
def show_all(contacts):
    list_of_contacts = list()
    for key, record in contacts.items():
       list_of_contacts.append(str(record))
    return list_of_contacts


@input_error
def add_birthday(args, book: AddressBook):
    name, birthday = args
    record = book.find(name)
    record.add_birthday(birthday)
    book.update_record(record)
    return "Contact updated"


@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    return f"Name: {record.name}, Birthday: {record.birthday}"


@input_error
def birthdays(args, book):
    upcoming_birthdays = book.get_upcoming_birthdays()
    return upcoming_birthdays


def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_phone(args, book))
        elif command == "all":
            list_of_contacts = show_all(book)
            for item in list_of_contacts:
                print(item)
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(args, book))
        elif command == "help":
            print("'close', 'exit' to stop the program")
            print("'add' to create new contact")
            print("'change' to change a contact")
            print("'phone' to see a phone number of person")
            print("'all' to print all contacts")
            print("'add-birthday' to add a new birthday to the contact")
            print("'show-birthday' to show date of birthday of the contact")
            print("'birthdays' to see all upcoming birthdays in next 7 days")
        else:
            print("Invalid command.")
            print("Try 'help' command")

if __name__ == "__main__":
    main()


