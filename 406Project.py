class Member():
    def __init__(self, id, name, phone_num, address, fee, attended_class, paid_for_class, total_payments) -> None:
        self.id = id
        self.name = name
        self.phone_number = phone_num
        self.address = address
        self.fee = fee
        self.attended_class = attended_class # Dictionary containing {class : attended (True/False)} pairs
        self.paid_for_class = paid_for_class # Dictionary containing {class : payment (>= 0)} pairs (0 -> didn't pay for class)
        self.total_payments = total_payments # Number of times paid (integer)
        self.current_payment = fee # Payment to pay for this session/week (fee by default, will change if discount given)
    
    def getId(self) -> str:
        return self.id
    
    def getName(self) -> str:
        return self.name

    def getPhoneNumber(self) -> str:
        return self.phone_number
    
    def getAddress(self) -> str:
        return self.address
    
    def getFee(self) -> float:
        return self.fee
    
    def getAttendedClass(self) -> dict:
        return self.attended_class
    
    def getPaidForClass(self) -> dict:
        return self.paid_for_class

    def getTotalPayments(self) -> int:
        return self.total_payments
    
    def getCurrentPayment(self) -> float:
        return self.current_payment

    def applyDiscount(self, discount) -> None:
        self.current_payment = round(self.fee * (1 - discount), 2)
    
    def attendClass(self, class_name) -> int: # Return -> (1 = successfully attended class | 0 = already attended class | -1 = class doesn't exist)
        if class_name in self.attended_class:
            if self.attended_class[class_name] == False: # Haven't yet attended class
                self.attended_class[class_name] = True
                return 1
            else: # Have already attended class
                return 0
        else: # Class doesn't exist
            return -1
    
    def payForClass(self, class_name) -> int: # Return -> (1 = successfully paid | 0 = already paid | -1 = class doesn't exist)
        if class_name in self.paid_for_class:
            if self.paid_for_class[class_name] == 0: # Haven't yet paid for class
                self.paid_for_class[class_name] = self.current_payment
                self.current_payment = self.fee # Resetting current_payment incase it has a 1-class 10% discount
                self.total_payments += 1
                return 1
            else: # Already paid for class
                return 0
        else: # Class doesn't exist
            return -1
    
    def addClass(self, class_name) -> bool:
        if class_name not in self.attended_class:
            self.attended_class[class_name] = False
            self.paid_for_class[class_name] = 0 # attended_class and paid_for_class should always have the same keys (classes)
            return True
        else:
            return False
        
    def toString(self):
        print(f"Id: {self.id} | Name: {self.name} | Phone Number: {self.phone_number} | Address: {self.address} | Fee: {self.fee} | Current Payment: {self.current_payment} | Total Payments: {self.total_payments}")
        print(f"\tAttended Class: {self.attended_class}")
        print(f"\tPaid For Class: {self.paid_for_class}")

class Members():
    def __init__(self, member_list=[]) -> None:
        self.member_list = member_list
        self.id = 0 # Will automatically assign a new id to each new member, then increment the id variable so no 2 members have the same id

    def getMembers(self) -> list[Member]:
        return self.member_list

    def addMember(self, name, phone_num, address, fee, attended_class, paid_for_class, total_payments) -> None: # Maybe add members through Members class to ensure that the id is correct
        self.member_list.append(Member(self.id, name, phone_num, address, fee, attended_class, paid_for_class, total_payments))
        self.id += 1
    
    def addMembers(self, member_list) -> None: # member_list is a list of member objects (may remove this function)
        self.member_list = self.member_list + member_list
    
    def validId(self, id) -> bool:
        return 0 <= id < self.id

    def printMembers(self) -> None:
        for member in self.member_list:
            member.toString()

    def attendClass(self, id, class_name) -> bool:
        if self.validId(id):
            result = self.member_list[id].attendClass(class_name)
            match result:
                case 1:
                    print(f"{self.member_list[id].getName()} ({self.member_list[id].getId()}) successfully attended class: {class_name}")
                    return True
                case 0:
                    print(f"{self.member_list[id].getName()} ({self.member_list[id].getId()}) has already attended class: {class_name}")
                    return False
                case -1:
                    print(f"Class ({class_name}) does not exist")
                    return False
        else:
            print(f"Id ({id}) is not valid")
            return False

    def makePayment(self, id, class_name) -> bool: # Will need a make 1 month payment method probably
        if self.validId(id):
            result = self.member_list[id].payForClass(class_name)
            match result:
                case 1:
                    print(f"{self.member_list[id].getName()} ({self.member_list[id].getId()}) successfully paid for class: {class_name}")
                    return True
                case 0:
                    print(f"{self.member_list[id].getName()} ({self.member_list[id].getId()}) has already paid for class: {class_name}")
                    return False
                case -1:
                    print(f"Class ({class_name}) does not exist")
                    return False
        else:
            print(f"Id ({id}) is not valid")
            return False

    def sortByAttendance(self) -> list[Member]: # Sorts and returns member list based on how many classes were attended (higher -> lower)
        return sorted(self.member_list, key=lambda x: (list(x.getAttendedClass().values())).count(True), reverse=True)
    
    def sortByPaid(self) -> list[Member]:
        return sorted(self.member_list, key=lambda x: x.getTotalPayments(), reverse=True)
    
    def giveDiscount(self) -> None:
        sorted_members = (self.sortByAttendance())[:10] # First 10 members with highest attendances
        for member in sorted_members:
            member.applyDiscount(0.1) # Give 10% discount for current payment (one class)

    def addClass(self, class_name) -> None: # Adds a class to the schedules of all members in the member list
        for member in self.member_list:
            member.addClass(class_name) # Can check for True/False returned here, if needed
    
    def checkPaid(self) -> list[Member]: # Returns a list of members that have not paid for a class (paid_for_class entry remains 0) more than once
        return list(filter(lambda x: (list(x.getPaidForClass.values())).count(0) > 1, self.member_list))
    
    def CheckConsistentPayment(self) -> None: # Applies a 1-class 10% discount to members who have consistently paid for their last 3 classes
        for member in self.member_list:
            if len(list(member.getPaidForClass().values())) >= 3: # Member has attended at least 3 classes
                if 0 not in (list(member.getPaidForClass().values())[-3:]): # Member has consistently paid for the last 3 classes
                    member.applyDiscount(0.1)


if __name__ == "__main__":
    # l = Members()
    #m1 = Member("John", "123", "Apple St", 10.00, {}, {}, 0)
    #m2 = Member("Jane", "456", "Coconut St", 9.00, {}, {}, 0)
    #m3 = Member("Bob", "789", "Banana St", 11.00, {}, {}, 0)
    # l.addMember("John", "123", "Apple St", 10.00, {}, {}, 0)
    # l.addMember("Jane", "456", "Coconut St", 9.00, {}, {}, 0)
    # l.addMember("Bob", "789", "Banana St", 11.00, {}, {}, 0)
    #print(l)
    #print(l.getMembers())
    # l.addClass("Week 1")
    # l.addClass("Week 2")
    # l.addClass("Week 2")
    # l.makePayment(1, 'Week 1')
    # l.attendClass(1, 'Week 1')
    #l.attendClass(0, 'Week 1')
    # l.makePayment(2, 'Week 2')
    # l.makePayment(3, 'Week 2')
    # l.makePayment(2, 'Week 3')
    # print(Members(l.sortByAttendance()).printMembers())
    # print(Members(l.sortByPaid()).printMembers())
    # l.printMembers()
    pass
