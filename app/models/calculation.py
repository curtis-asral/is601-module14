from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Calculation(Base):
    __tablename__ = "calculations"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String)
    inputs = Column(JSON)
    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "calculation"}

    @staticmethod
    def create(calc_type, user_id, inputs):
        if calc_type == "addition":
            return Addition(user_id=user_id, inputs=inputs)
        if calc_type == "subtraction":
            return Subtraction(user_id=user_id, inputs=inputs)
        if calc_type == "multiplication":
            return Multiplication(user_id=user_id, inputs=inputs)
        if calc_type == "division":
            return Division(user_id=user_id, inputs=inputs)
        return Calculation(user_id=user_id, inputs=inputs)

    def get_result(self):
        return None

class Addition(Calculation):
    __mapper_args__ = {"polymorphic_identity": "addition"}
    def get_result(self):
        return sum(self.inputs)

class Subtraction(Calculation):
    __mapper_args__ = {"polymorphic_identity": "subtraction"}
    def get_result(self):
        result = self.inputs[0]
        for value in self.inputs[1:]:
            result -= value
        return result

class Multiplication(Calculation):
    __mapper_args__ = {"polymorphic_identity": "multiplication"}
    def get_result(self):
        result = 1
        for value in self.inputs:
            result *= value
        return result

class Division(Calculation):
    __mapper_args__ = {"polymorphic_identity": "division"}
    def get_result(self):
        result = self.inputs[0]
        for value in self.inputs[1:]:
            if value == 0:
                raise ValueError()
            result /= value
        return result
