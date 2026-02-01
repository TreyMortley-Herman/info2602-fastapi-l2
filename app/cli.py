import typer
from app.database import create_db_and_tables, get_session, drop_all
from app.models import User
from fastapi import Depends
from sqlmodel import select
from sqlalchemy.exc import IntegrityError

cli = typer.Typer()

@cli.command()
def initialize():
    with get_session() as db: # Get a connection to the database
        drop_all() # delete all tables
        create_db_and_tables() #recreate all tables
        bob = User(username='bob', email='bob@mail.com', password='bobpass') # Create a new user (in memory)
        db.add(bob) # Tell the database about this new data
        db.commit() # Tell the database persist the data
        db.refresh(bob) # Update the user (we use this to get the ID from the db)
        print("Database Initialized")


#Exercise 1: Find users by partial match in username or email
@cli.command()
def get_user(query: str = typer.Argument(..., help="Partial username or email to search for")):
    with get_session() as db:
        users = db.exec(
            select(User).where(
                (User.username.contains(query)) | (User.email.contains(query))
            )
        ).all()
        if not users:
            print(f'No users found matching "{query}"')
            return
        for user in users:
            print(user)

# Exercise 2: Paginated list of users
@cli.command()
def get_all_users(
    limit: int = typer.Option(10, help="Number of users to return"),
    offset: int = typer.Option(0, help="Number of users to skip")
):
    with get_session() as db:
        all_users = db.exec(
            select(User).offset(offset).limit(limit)
        ).all()
        if not all_users:
            print("No users found")
            return
        for user in all_users:
            print(user)

@cli.command()
def change_email(
    username: str = typer.Argument(..., help="Username of the user to update"),
    new_email: str = typer.Argument(..., help="New email address for the user")
):
    
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to update email.')
            return
        user.email = new_email
        db.add(user)
        db.commit()
        print(f"Updated {user.username}'s email to {user.email}")


@cli.command()
def create_user(
    username: str = typer.Argument(..., help="Username for the new user"),
    email: str = typer.Argument(..., help="Email for the new user"),
    password: str = typer.Argument(..., help="Password for the new user")
):
    
    with get_session() as db: # Get a connection to the database
        newuser = User(username, email, password)
        try:
            db.add(newuser)
            db.commit()
        except IntegrityError as e:
            db.rollback() #let the database undo any previous steps of a transaction
            #print(e.orig) #optionally print the error raised by the database
            print("Username or email already taken!") #give the user a useful message
        else:
            print(newuser) # print the newly created user


@cli.command()
def delete_user(username: str = typer.Argument(..., help="Username of the user to delete")):
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to delete user.')
            return
        db.delete(user)
        db.commit()
        print(f'{username} deleted')


if __name__ == "__main__":
    cli()