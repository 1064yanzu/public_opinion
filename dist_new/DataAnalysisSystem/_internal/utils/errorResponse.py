from flask import render_template

def errorResponse(error_message):
    return render_template('error.html',error_message=error_message)