# Portfolio Webapp

**A #100DaysOfCode Portfolio Project**

<hr>

This web application is written in Python and utilizes the Flask framework to serve my personal portfolio website HTML. 
Authentication for blog posts and comments is secured using salted and hashed passwords. SQLAlchemy handles the 
interactions with a relational database. Email is handled by smtplib.

The front end consists of HTML, Jinja templating, and Bootstrap CSS for styling. A small amount of Bootstrap Javascript 
is employed for website functionality.

A GitHub Action deploys changes to the webapp and associated templates to AWS Elastic Beanstalk using the EB CLI tool. 
Elastic Beanstalk automatically provisions and configures the necessary resources to run the web application. 