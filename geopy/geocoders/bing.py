"""
:class:`.Bing` geocoder.
"""

from geopy.compat import urlencode
from geopy.geocoders.base import Geocoder, DEFAULT_FORMAT_STRING, \
    DEFAULT_TIMEOUT, DEFAULT_SCHEME
from geopy.location import Location
from geopy.util import logger, join_filter


__all__ = ("Bing", )


class Bing(Geocoder):
    """
    Geocoder using the Bing Maps Locations API. Documentation at:
        https://msdn.microsoft.com/en-us/library/ff701715.aspx
    """

    def __init__(
            self,
            api_key,
            format_string=DEFAULT_FORMAT_STRING,
            scheme=DEFAULT_SCHEME,
            timeout=DEFAULT_TIMEOUT,
            proxies=None,
        ):  # pylint: disable=R0913
        """Initialize a customized Bing geocoder with location-specific
        address information and your Bing Maps API key.

        :param string api_key: Should be a valid Bing Maps API key.

        :param string format_string: String containing '%s' where the
            string to geocode should be interpolated before querying the
            geocoder. For example: '%s, Mountain View, CA'. The default
            is just '%s'.

        :param string scheme: Use 'https' or 'http' as the API URL's scheme.
            Default is https. Note that SSL connections' certificates are not
            verified.

            .. versionadded:: 0.97

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception.

            .. versionadded:: 0.97

        :param dict proxies: If specified, routes this geocoder's requests
            through the specified proxy. E.g., {"https": "192.0.2.0"}. For
            more information, see documentation on
            :class:`urllib2.ProxyHandler`.

            .. versionadded:: 0.96
        """
        super(Bing, self).__init__(format_string, scheme, timeout, proxies)
        self.api_key = api_key
        self.api = "%s://dev.virtualearth.net/REST/v1/Locations" % self.scheme

    def geocode(
            self,
            query,
            exactly_one=True,
            user_location=None,
            timeout=None,
            culture=None,
            include_neighborhood=None,
            include_country_code=False,
            restrict_to=None
            ):  # pylint: disable=W0221
        """
        Geocode an address.

        :param string query: The address or query you wish to geocode.

        :param bool exactly_one: Return one result or a list of results, if
            available.

        :param user_location: Prioritize results closer to
            this location.

            .. versionadded:: 0.96

        :type user_location: :class:`geopy.point.Point`

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

            .. versionadded:: 0.97

        :param string culture: Affects the language of the response,
            must be a two-letter country code.

            .. versionadded:: 1.4.0

        :param boolean include_neighborhood: Sets whether to include the
            neighborhood field in the response.

            .. versionadded:: 1.4.0

        :param boolean include_country_code: Sets whether to include the
            two-letter ISO code of the country in the response (field name
            'countryRegionIso2').

            .. versionadded:: 1.4.0

        :param restrict_to: Restricts results to a subset of location
        types. e.g. ['Address', 'CountryRegion']

        """
        params = {
            'query': self.format_string % query,
            'key': self.api_key
        }
        if user_location:
            params['userLocation'] = ",".join(
                (str(user_location.latitude), str(user_location.longitude))
            )
        if exactly_one is True:
            params['maxResults'] = 1
        if culture:
            params['culture'] = culture
        if include_neighborhood is not None:
            params['includeNeighborhood'] = include_neighborhood
        if include_country_code:
            params['include'] = 'ciso2'  # the only acceptable value

        url = "?".join((self.api, urlencode(params)))
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout),
            exactly_one=exactly_one,
            restrict_to=restrict_to
        )

    def reverse(self, query, exactly_one=True, timeout=None):
        """
        Reverse geocode a point.

        :param query: The coordinates for which you wish to obtain the
            closest human-readable addresses.
        :type query: :class:`geopy.point.Point`, list or tuple of (latitude,
            longitude), or string as "%(latitude)s, %(longitude)s".

        :param bool exactly_one: Return one result, or a list?

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

            .. versionadded:: 0.97
        """
        point = self._coerce_point_to_string(query)
        params = {'key': self.api_key}
        url = "%s/%s?%s" % (
            self.api, point, urlencode(params))

        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_json(
            self._call_geocoder(url, timeout=timeout),
            exactly_one=exactly_one
        )

    @staticmethod
    def _parse_json(doc, exactly_one=True, restrict_to=None):  # pylint: disable=W0221
        """
        Parse a location name, latitude, and longitude from an JSON response.
        """
        resources = doc['resourceSets'][0]['resources']
        if resources is None or not len(resources): # pragma: no cover
            return None

        def parse_resource(resource):
            """
            Parse each return object.
            """
            stripchars = ", \n"
            addr = resource['address']

            address = addr.get('addressLine', '').strip(stripchars)
            city = addr.get('locality', '').strip(stripchars)
            state = addr.get('adminDistrict', '').strip(stripchars)
            zipcode = addr.get('postalCode', '').strip(stripchars)
            country = addr.get('countryRegion', '').strip(stripchars)

            city_state = join_filter(", ", [city, state])
            place = join_filter(" ", [city_state, zipcode])
            location = join_filter(", ", [address, place, country])

            latitude = resource['point']['coordinates'][0] or None
            longitude = resource['point']['coordinates'][1] or None
            if latitude and longitude:
                latitude = float(latitude)
                longitude = float(longitude)
            entity_type = resource['entityType']

            return Location(location, (latitude, longitude), resource)

        parsed_resources = [
            parse_resource(resource)
            for resource in resources

            if restrict_to is None or resource['entityType'] in restrict_to]

        if not parsed_resources:
            return None

        if exactly_one:
            return parsed_resources[0]
        else:
            return parsed_resources
