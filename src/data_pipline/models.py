""" Store Dataclasses for the Attendance events"""


from dataclasses import dataclass, field


@dataclass
class Person:
    person_id: str





@dataclass
class Session:
    session_id: str
    date: str
    time: str




class DanceSession(Session):
    """   Model the default Dance session"""



