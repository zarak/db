from flask_testing import TestCase
from app import db, app
from models.datapoint import Datapoint


class DbTest(TestCase):

    DATABASE_URI = 'sqlite:///:memory:'

    def create_app(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = DbTest.DATABASE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
        return app

    def setUp(self):
        print("BASE SETUP")
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()


class BasicFilledDbSetup(DbTest):

    def setUp(self):
        super(BasicFilledDbSetup, self).setUp()
        print("CHILD SETUP")
        x1 = Datapoint(date="2014-03-31", freq='q', name="CPI_rog", value=102.3)
        x2 = Datapoint(date="2017-03-16", freq='d', name="BRENT", value=50.56)
        db.session.add(x1)
        db.session.add(x2)
        db.session.commit()
        db.session.close()


class DbEmpty(DbTest):

    def test_initial_table_is_empty(self):
        count = Datapoint.query.count()
        assert count == 0


class BasicFilledDbUpdate(BasicFilledDbSetup):

    def test_update(self):
        # no specified data in DB currently
        result = Datapoint.query\
            .filter_by(value=(50.56+10))\
            .all()
        assert len(result) == 0

        # update 1 row with specified data
        Datapoint.query.filter(Datapoint.name == "BRENT")\
            .update({"value": (50.56 + 10.0)})

        # test there's 1 row having specified data after update
        result = Datapoint.query\
            .filter_by(value=(50.56 + 10))\
            .all()

        assert len(result) == 1
        datapoint = result[0]
        assert datapoint.name == "BRENT"
        assert datapoint.value == '60.56'


class BasicFilledDbDelete(BasicFilledDbSetup):

    def test_delete(self):
        count = Datapoint.query.count()
        assert count == 2

        Datapoint.query\
            .filter(Datapoint.value == "102.3")\
            .delete()

        count = Datapoint.query.count()
        assert count == 1


class BasicFilledDbRead(BasicFilledDbSetup):

    def test_read(self):
        datapoints = Datapoint.query.all()
        assert len(datapoints) == 2

        x1 = Datapoint(date="2014-03-31", freq='q', name="CPI_rog", value=102.3)
        x2 = Datapoint(date="2017-03-16", freq='d', name="BRENT", value=50.56)

        for dp in datapoints:
            assert (dp.date == x1.date and dp.freq == x1.freq and dp.name == x1.name and float(dp.value) == x1.value) \
                   or (dp.date == x2.date and dp.freq == x2.freq and dp.name == x2.name and float(dp.value) == x2.value)