# Item Catalog Application
Udacity Project - Item Catalog Application

This project demonstrates CRUD in a web application using Flask and SqlAlchemy.

## Getting Started

Follow these instructions in order to make this test this application.

### Prerequisites

#### Programming Language:

[Python](https://www.python.org/)

#### Virtual Machine

Please fork this repository.

On your terminal type this command: `cd vagrant/catalog`

Then initialize the virtual machine by `vagrant up` then `vagrant ssh`


## Setting up the Application

After performing the previous steps, type this in your terminal: `cd \vagrant`

Now type: `python items.py` to load some sample data in the db

And then type:  `python application.py`

## To Test the Application

In your browser, go to `http://localhost:5000` and test the app.

To test the sample json endpoints, enter these url on a browser:
(Be sure to substitute a real category id in the place of: `<int:category_id>`)

`http://localhost:5000/category/JSON`
`http://localhost:5000/category/<int:category_id>/items/JSON`
`http://localhost:5000/category/<int:category_id>/item/<int:item_id>/JSON`
