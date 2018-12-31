from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Base, Item, User
import datetime

engine = create_engine('sqlite:///catalog.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()


User1 = User(name="Freddy Freeman", email="ffreeman@awesome.com",
             picture='https://fontawesome.com/icons/user?style=solid')
session.add(User1)
session.commit()

# Baseball
category1 = Category(user_id=1, name="Baseball")

session.add(category1)
session.commit()

item1 = Item(
    user_id=1, name="Wood Bat", description="Perfect for hitting homeruns!",
    price="84.99", category=category1, created_date=datetime.datetime.now()
    )

session.add(item1)
session.commit()


item2 = Item(
    user_id=1, name="Glove", description="Made of the finest leather for catching any ball!",
    price="74.99", category=category1, created_date=datetime.datetime.now()
    )

session.add(item2)
session.commit()

item3 = Item(
    user_id=1, name="Hat", description="Perfect for keeping the sun out of your face!",
    price="24.99", category=category1, created_date=datetime.datetime.now()
    )

session.add(item3)
session.commit()


# Basketball
category2 = Category(user_id=1, name="Basketball")

session.add(category2)
session.commit()


item1 = Item(
    user_id=1, name="Jersey", description="Made of the upmost quality!",
    price="64.99", category=category2, created_date=datetime.datetime.now()
    )

session.add(item1)
session.commit()

item2 = Item(
    user_id=1, name="Ball", description="Professional size, weight, and dimension!",
    price="25.99", category=category2, created_date=datetime.datetime.now()
    )

session.add(item2)
session.commit()

item3 = Item(
    user_id=1, name="Shoes", description="Perfect for anyone who wants to dunk!",
    price="98.99", category=category2, created_date=datetime.datetime.now()
    )

session.add(item3)
session.commit()

# Golf
category3 = Category(user_id=1, name="Golf")

session.add(category3)
session.commit()


item1 = Item(
    user_id=1, name="Clubs", description="Perfect set of clubs for the serious golfer!",
    price="299.99", category=category3, created_date=datetime.datetime.now()
    )

session.add(item1)
session.commit()

item2 = Item(
    user_id=1, name="Balls", description="Gets the farthest air time compared to any other ball!",
    price="32.99", category=category3, created_date=datetime.datetime.now()
    )

session.add(item2)
session.commit()


item3 = Item(
    user_id=1, name="Bag", description="Designed to hold and protect your most valuable clubs!",
    price="99.99", category=category3, created_date=datetime.datetime.now()
    )

session.add(item3)
session.commit()


print "Items added to the Catalog!"
