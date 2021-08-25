from flask import Flask, render_template, request
import redis

app = Flask(__name__)

app.config['SQLALCHEMY_DATABSE_URI'] = 'postgresql://hello_flask:hello_flask@db:5432/hello_flask_dev'

from app.models import db, UserFavs

db.init_app(app)
with app.app_context():
    db.create_all()
    db.session.commit()

red = redis.Redis(host='redis', port=6379)

@app.route("/")
def main():
    return render_template('index.html')

@app.route('/save', methods=['POST'])
def save():
    username = request.form['username']
    place = request.form['place']
    food = request.form ['food']

    print('username', username)
    print('place', place)
    print('food', food)

    #check if username exits in redis
    if red.hgetall(username).keys():
        print('hget username:', red.hgetall(username))
        return render_template('index.html', user_exists=1,msg='(From Redis)', username=username, place=red.hget(username,'place').decode('utf-8'), food=red.hget(username,'food').decode('utf-8'))
        #if not in redis, then check in db
    elif len(list(red.hgetall(username).keys()))==0:
        print('no such username')
        record = UserFavs.query.filter_by(username=username).first()
        print('Records fetched from db:', record)

        if record: 
            red.hset(username, 'place', record.place)
            red.hset(username, 'food', record.food)

            return render_template('index.html', user_exists=1, msg='(From DataBase)', username=username, place=record.place, food=record.food)

    #if fate of the username doesnt exit either in redis or in db
    #create a new record into db and store the dara in redis as well
    new_record= UserFavs(username=username, place=place, food=food)
    db.session.add(new_record)
    db.session.commit()

    #store in redis for faster acceess
    red.hset(username, 'place', place)
    red.hset(username, 'food', food)

    #check to see if its in the db and insert it
    record = UserFavs.query.filter_by(username=username).first()
    print('Records fetched from db after insert:', record)

    #check insert operation in redis
    print('Username from redis after insert:', red.hgetall(username))
    #rendering template that is saved, and returning the information back onto the screenß
    return render_template('index.html', saved=1, username=username, place=red.hget(username,'place').decode('utf-8'), food=red.hget(username,'food').decode('utf-8'))

    # get all the keys from the database thats been stored till now
@app.route('/keys', methods=['GET'])
def keys():
    records = UserFavs.query.all() #gets all records. 
    names =[]
    for record in records: #from all sets of records, we are recieveing each record of the usernames and appending to the stored list
        names.append(record.username)
    return render_template('index.html', keys=1, usernames=names)
    
# if information is not in the redis, we check the DB, if not or message will show its not there
@app.route('/get', methods=['POST'])
def get():
    username = request.form['username']
    print('Username', username)
    user_data = red.hgetall(username)
    print('GET Redis:', user_data)

    if not user_data:
        record = UserFavs.query.filter_by(username=username).first()
        print('GET Record:', record) 
        if not record:
            print('No Data in redis or db')
            return render_template('index.html', no_record=1, msg=f'Record not yet defined for {username}')
        red.hset(username, 'place', record.place)
        red.hset(username, 'food', record.food)
        return render_template('index.html', get=1, msg='(From DataBase)', username=username, place=record.place, food=record.food)
    return render_template('index.html', get=1, msg='(From Database)', username=username, place=user_data[b'place'].decode('utf-8'), food=user_data[b'food'].decode('utf-8'))


# if __name__ == "__main__":
#     # Only for debugging while developing
#     app.run(host='0.0.0.0', debug=True, port=80)