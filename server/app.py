#!/usr/bin/env python3

from flask import Flask, request, make_response, jsonify
from flask_migrate import Migrate
from flask_restful import Api, Resource
from models import db, Hero, Power, HeroPower
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get(
    "DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)
api = Api(app)

class Home(Resource):
     def get(self):
          return '<h1>Code challenge</h1>'

class HeroesData(Resource):
     def get(self):
        heroes = Hero.query.all()
        return [hero.to_dict(rules={'-hero_powers': True}) for hero in heroes], 200

class IndividualHero(Resource):
     def get(self, id):
        hero = db.session.get(Hero, id)
        if hero is None:
            return {"error": "Hero not found"}, 404
        return hero.to_dict(), 200     

class PowersData(Resource):
    def get(self):
        powers = Power.query.all()
        return [power.to_dict(rules={'-hero_powers': True}) for power in powers], 200

class PowerById(Resource):
    def get(self, id):
        power = db.session.get(Power, id)
        if power is None:
            return {"error": "Power not found"}, 404
        return power.to_dict(rules={'-hero_powers': True}), 200
    
    def patch(self, id):
        power = db.session.get(Power, id)
        if power is None:
            return {"error": "Power not found"}, 404
        data = request.get_json()

        description = data.get('description')
        if description is not None:
            if len(description) < 20:
                return {"errors": ["validation errors"]}, 400
            power.description = description
            db.session.commit()
        
        return power.to_dict(), 200

class CreateHeroPower(Resource):
    def post(self):
        try:
            data = request.get_json()
            strength = data.get('strength')
            hero_id = data.get('hero_id')
            power_id = data.get('power_id')

            allowed_strengths = ['Weak', 'Average', 'Strong']
            if strength not in allowed_strengths:
                return {"errors": ["validation errors"]}, 400

            hero = db.session.get(Hero, hero_id) 
            power = db.session.get(Power, power_id) 
            if not hero or not power:
                return {"error": "Hero or Power not found"}, 404

            hero_power = HeroPower.query.filter_by(
                hero_id=hero_id, power_id=power_id).one_or_none()
            if hero_power:
                db.session.delete(hero_power)
                db.session.commit()

            hero_power = HeroPower(strength=strength, hero_id=hero_id, power_id=power_id)
            db.session.add(hero_power)
            db.session.commit()

            return jsonify({
                'id': hero_power.id,
                'strength': hero_power.strength,
                'hero_id': hero_power.hero_id,
                'power_id': hero_power.power_id,
                'hero': hero.to_dict(),
                'power': power.to_dict()
            })

        except Exception as e:
            print(f"Exception occurred: {e}")
            return {"error": "Internal Server Error"}, 500

api.add_resource(Home, '/')
api.add_resource(HeroesData, '/heroes')
api.add_resource(IndividualHero, '/heroes/<int:id>')
api.add_resource(PowersData, '/powers')
api.add_resource(PowerById, '/powers/<int:id>')
api.add_resource(CreateHeroPower, '/hero_powers')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
