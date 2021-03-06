
import unittest
import types

from geopy import exc
from geopy.point import Point
from geopy.geocoders import GeocodeFarm
from test.geocoders.util import GeocoderTestBase, env


@unittest.skipUnless(  # pylint: disable=R0904,C0111
    bool(env.get('GEOCODEFARM_KEY')),
    "GEOCODEFARM_KEY env variable not set"
)
class GeocodeFarmTestCase(GeocoderTestBase): # pylint: disable=R0904,C0111

    @classmethod
    def setUpClass(cls):
        cls.delta = 0.04
        cls.geocoder = GeocodeFarm(
            api_key=env['GEOCODEFARM_KEY'],
            format_string="%s US"
        )

    def test_geocode(self):
        """
        OpenCage.geocode
        """
        self.geocode_run(
            {"query": u"435 north michigan ave, chicago il 60611 usa"},
            {"latitude": 41.890, "longitude": -87.624},
        )

    def test_reverse_string(self):
        """
        GeocodeFarm.reverse string
        """
        self.reverse_run(
            {"query": u"40.75376406311989,-73.98489005863667"},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )

    def test_reverse_point(self):
        """
        GeocodeFarm.reverse Point
        """
        self.reverse_run(
            {"query": Point(40.75376406311989, -73.98489005863667)},
            {"latitude": 40.75376406311989, "longitude": -73.98489005863667},
        )

    def test_authentication_failure(self):
        """
        GeocodeFarm authentication failure
        """
        self.geocoder = GeocodeFarm(api_key="invalid")
        with self.assertRaises(exc.GeocoderAuthenticationFailure):
            address = '435 north michigan ave, chicago il 60611'
            self.geocoder.geocode(address)

    def test_quota_exceeded(self):
        """
        GeocodeFarm quota exceeded
        """

        def mock_call_geocoder(*args, **kwargs):
            """
            Mock API call to return bad response.
            """
            return {
                "geocoding_results": {
                    "STATUS": {
                        "access": "OVER_QUERY_LIMIT",
                        "status": "FAILED, ACCESS_DENIED"
                    }
                }
            }
        self.geocoder._call_geocoder = types.MethodType(
            mock_call_geocoder,
            self.geocoder
        )

        with self.assertRaises(exc.GeocoderQuotaExceeded):
            self.geocoder.geocode(u'435 north michigan ave, chicago il 60611')

    def test_unhandled_api_error(self):
        """
        GeocodeFarm unhandled error
        """

        def mock_call_geocoder(*args, **kwargs):
            """
            Mock API call to return bad response.
            """
            return {
                "geocoding_results": {
                    "STATUS": {
                        "access": "BILL_PAST_DUE",
                        "status": "FAILED, ACCESS_DENIED"
                    }
                }
            }
        self.geocoder._call_geocoder = types.MethodType(
            mock_call_geocoder,
            self.geocoder
        )

        with self.assertRaises(exc.GeocoderServiceError):
            self.geocoder.geocode(u'435 north michigan ave, chicago il 60611')
