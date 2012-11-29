## Dependencies in virtualenv

    mkvirtualenv buildbot_forcebuild_service
    workon buildbot_forcebuild_service
    pip install -r requirements.txt

## To start

    twistd buildbot-forcebuild

## Parameters

    ['port',    'p', 4000, 'The port number to listen on.'],
    ['pb-host', 'H', '127.0.0.1', 'The buildmaster PB host to connect to'],
    ['pb-port', 'P', 9989, 'The buildmaster PB port to connect to'],
    ['pb-user', 'user', 'change', 'The buildmaster PB username'],
    ['pb-pass', 'pass', 'changepw', 'The buildmaster PB password'],
    ['blocking', 'b', False, 'Block on HTTP request ?'],
