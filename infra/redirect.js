var REDIRECT_HOSTS = {
  'www.thatsacleanrock.earth': true,
  'thatsacleanrock.com': true,
  'www.thatsacleanrock.com': true,
};

function handler(event) {
  var request = event.request;
  var host = request.headers.host.value;

  if (REDIRECT_HOSTS[host]) {
    return {
      statusCode: 301,
      statusDescription: 'Moved Permanently',
      headers: {
        location: { value: 'https://thatsacleanrock.earth' + request.uri }
      }
    };
  }

  return request;
}
