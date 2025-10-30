from flask_restx import Resource, fields
from flask import request
from app.api.v1 import api, events_ns
from app.services.event_service import EventService


event_service = EventService()

event_create_model = api.model('EventCreate', {
    'scope': fields.String(required=True, enum=['INDIVIDUAL','GROUP']),
    'animal_type': fields.String(enum=['RABBIT','COW','CHICKEN','SHEEP','OTHER']),
    'name': fields.String(enum=['MAINTENANCE','VITAMINS','FENCING','OTHER']),
    'date': fields.String(description='ISO date time'),
    'description': fields.String,
    'animal_id': fields.String,
    'corral_id': fields.String,
    'rabbit_event': fields.String(enum=['MAINTENANCE_CAGES','MAINTENANCE_TANKS','VITAMINS_CORRAL','SLAUGHTER','OTHER']),
    'chicken_event': fields.String(enum=['MAINTENANCE_FENCE','VITAMINS_CORRAL','OTHER']),
    'cow_event': fields.String(enum=['VITAMINS','DEWORMING','OTHER']),
    'sheep_event': fields.String(enum=['VITAMINS','DEWORMING','OTHER']),
})


@events_ns.route('/')
class EventList(Resource):
    @events_ns.doc('list_events')
    def get(self):
        params = {
            'species': request.args.get('species'),
            'scope': request.args.get('scope'),
            'from': request.args.get('from'),
            'to': request.args.get('to'),
            'animal_id': request.args.get('animal_id'),
            'corral_id': request.args.get('corral_id'),
        }
        data, status = event_service.list_events(params)
        return data, status

    @events_ns.doc('create_event')
    @events_ns.expect(event_create_model)
    def post(self):
        payload = request.get_json() or {}
        data, status = event_service.create_event(payload)
        return data, status
