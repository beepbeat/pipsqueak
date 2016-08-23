import ratlib
import ratlib.api
import ratlib.api.http
import functools

urljoin = ratlib.api.http.urljoin
savedratids = {}
savedratnames = {}
savedclientnames = {}

def getRatId(bot, ratname, platform=None):

    if ratname in savedratids.keys():
        if platform == None:
            return savedratids.get(ratname)
        if platform == getRatName(bot, ratid=savedratids.get(ratname)['id'])[1]:
            return savedratids.get(ratname)


    try:
        uri = '/users?nicknames=' + ratname
        # print('looking for name '+ratname)
        # print('uri: '+str(uri))
        result = callapi(bot=bot, method='GET', uri=uri)
        # print(result)
        data = result['data']
        # print(data)
        returnlist = []
        if platform == None:
            firstmatch = data[0]
            id = firstmatch['CMDRs'][0]
            ratnam, ratplat = getRatName(bot, id)
            ret = {'id': id, 'name':ratnam , 'platform':firstmatch['platform']}

        else:
            ret = {'id':None, 'name':None, 'platform':None}
            id = None
            ratnam = None
            if len(data) == 0:
                # print('data length 0')
                raise Exception
            for user in data:
                for cmdr in user['CMDRs']:
                    ratnam, ratplat = getRatName(bot, cmdr)
                    rat = {'id':cmdr, 'platform':ratplat}
                    if rat['platform'] == platform:
                        id = rat['id']
                        ret = {'id':rat['id'], 'name': ratnam, 'platform':rat['platform']}
                        returnlist.append(ret)
            strippedname = removeTags(ratname)
            for retelement in returnlist:
                if (retelement['name']==ratname) or (retelement['name']==strippedname):
                    ret = retelement
        savedratids.update({ratname: ret})
        savedratnames.update({id: {'name': ratnam, 'platform': ret['platform']}})
        return ret
    except:
        # print('didnt find with tags, trying without')
        try:
            strippedname = removeTags(ratname)
            if strippedname in savedratids.keys():
                return savedratids[strippedname]
            uri = '/users?nicknames=' + strippedname
            result = callapi(bot=bot, method='GET', uri=uri)
            print(result)
            data = result['data']
            # print(data)
            returnlist = []
            if platform == None:
                firstmatch = data[0]
                id = firstmatch['CMDRs'][0]
                ratnam, ratplat = getRatName(bot, id)
                ret = {'id': id, 'name': ratnam, 'platform': firstmatch['platform']}

            else:
                ret = {'id': None, 'name': None, 'platform': None}
                id = None
                if len(data) == 0:
                    # print('data length 0, calling fallback.')
                    return idFallback(bot, ratname, platform=platform)
                for user in data:
                    for cmdr in user['CMDRs']:
                        ratnam, ratplat = getRatName(bot, cmdr)
                        rat = {'id': cmdr, 'platform': ratplat}
                        if rat['platform'] == platform:
                            id = rat['id']
                            ret = {'id': rat['id'], 'name': ratnam, 'platform': rat['platform']}
                            returnlist.append(ret)
                strippedname = removeTags(ratname)
                for retelement in returnlist:
                    if (retelement['name'] == ratname) or (retelement['name'] == strippedname):
                        ret = retelement
            savedratids.update({strippedname: ret})
            savedratnames.update({id: {'name':ratnam, 'platform':ret['platform']}})
            return ret
        except:
            # print('Calling fallback on ratID search as no rat with registered nickname '+strippedname+' or '+ratname+' was found.')
            return idFallback(bot, ratname, platform=platform)


def idFallback(bot, ratname, platform=None):
    """
    Fallback to searching the commander Name instead of the linked account nickname.
    Args:
        bot: the bot to pull the config from
        ratname: the cmdrname to look for

    Returns:
        a dict with ['id'] which has the id it got, ['name'] the name it used to poll the api and
        if the api call returned an error or the rat wasn't found, ['error'] has the returned error object and
        ['description'] a description of the error.

    """
    strippedname = removeTags(ratname)

    try:
        uri = '/rats?CMDRname=' + strippedname + (('&platform='+platform) if platform is not None else '')
        result = callapi(bot=bot, method='GET', uri=uri)
        # print(result)
        data = result['data']
        # print(data)
        firstmatch = data[0]
        id = firstmatch['id']
        ret =  {'id': id, 'name': strippedname, 'platform':firstmatch['platform']}
        savedratids.update({ratname:ret})
        savedratnames.update({id:{'name':strippedname, 'platform':firstmatch['platform']}})
        return ret


    except IndexError as ex:
                # print('no rats with that commandername or nickname or gamertag found.')
                return {'id': '0', 'name': ratname, 'error': ex, 'platform':'unknown',
                        'description': 'no rats with that commandername or nickname or gamertag found.'}
    except ratlib.api.http.APIError as ex:
        print('APIError: couldnt find RatId for ' + ratname)
        return {'id': '0', 'name': ratname, 'platform':'unknown', 'error': ex, 'description': 'API Error while trying to fetch Rat'}


def getRatName(bot, ratid):
    """
    Returns the Name of a rat from its RatID by calling the API
    :param bot: the bot to pull config from and log errors to irc
    :param ratid: the id of the rat to find the name for
    :return: name of the rat
    """
    if str(ratid) in savedratnames.keys():
        return savedratnames.get(ratid)['name'], savedratnames.get(ratid)['platform']
    try:
        result = callapi(bot=bot, method='GET', uri='/rats/' + str(ratid))
    except ratlib.api.http.APIError:
        print('got Api error during api call')
        return 'unknown', 'unknown'
    try:
        data = result['data']
        name = data['CMDRname']
        platform = data['platform']
        ret = name, platform
    except:
        ret = 'unknown', 'unknown'
    # print('returning '+str(ret)+' as name for '+ratid)
    return ret

def removeTags(string):
    """
       Removes tags that are used on irc; ex: Marenthyu[PC] becomes Marenthyu
       :param string: the untruncated string
       :return: the string with everything start at an [ removed.
    """
    try:
        i = string.index('[')
    except ValueError:
        i = len(string)

    return string[0:i]

def callapi(bot, method, uri, data=None, _fn=ratlib.api.http.call):
    '''
    Calls the API with the gived method endpoint and data.
    :param bot: bot to pull config from and log error messages to irc
    :param method: GET PUT POST etc.
    :param uri: the endpoint to use, ex /rats
    :param data: body for request
    :param _fn: http call function to use
    :return: the data dict the api call returned.
    '''
    uri = urljoin(bot.config.ratbot.apiurl, uri)
    headers = {"Authorization": "Bearer " + bot.config.ratbot.apitoken}
    with bot.memory['ratbot']['apilock']:
        return _fn(method, uri, data, log=bot.memory['ratbot']['apilog'], headers=headers)

def getClientName(bot, resId):
    """
    Gets a client name from a rescueid
    :param bot: used to send messages and log errors to irc
    :param resId: the rescueid to look for the client's name
    :return: Client nickname of resId
    """

    if resId in savedclientnames.keys():
        return savedclientnames[resId]

    try:
        result = callapi(bot=bot, method='GET', uri='/rescues/' + resId)
        data = result['data']
        ret = data['client']['nickname']
    except:
        ret = 'unknown'
    savedclientnames.update({resId:ret})
    return ret

def flushNames():
    savedratids.clear()
    savedratnames.clear()
    savedclientnames.clear()

def require_netadmin(message=None):
    """Decorate a function to require the triggering user to be a FuelRats netadmin (as in, a highly ranked admin.).
    If they are not, `message` will be said if given."""
    def actual_decorator(function):
        @functools.wraps(function)
        def guarded(bot, trigger, *args, **kwargs):
            if getPrivLevel(trigger)<6:
                if message and not callable(message):
                    bot.say(message)
            else:
                return function(bot, trigger, *args, **kwargs)
        return guarded
    # Hack to allow decorator without parens
    if callable(message):
        return actual_decorator(message)
    return actual_decorator

def require_techrat(message=None):
    """Decorate a function to require the triggering user to be a FuelRats netadmin (as in, a highly ranked admin.).
    If they are not, `message` will be said if given."""
    def actual_decorator(function):
        @functools.wraps(function)
        def guarded(bot, trigger, *args, **kwargs):
            if getPrivLevel(trigger)<5:
                if message and not callable(message):
                    bot.say(message)
            else:
                return function(bot, trigger, *args, **kwargs)
        return guarded
    # Hack to allow decorator without parens
    if callable(message):
        return actual_decorator(message)
    return actual_decorator

def require_op(message=None):
    """Decorate a function to require the triggering user to be a FuelRats netadmin (as in, a highly ranked admin.).
    If they are not, `message` will be said if given."""
    def actual_decorator(function):
        @functools.wraps(function)
        def guarded(bot, trigger, *args, **kwargs):
            if getPrivLevel(trigger)<4:
                if message and not callable(message):
                    bot.say(message)
            else:
                return function(bot, trigger, *args, **kwargs)
        return guarded
    # Hack to allow decorator without parens
    if callable(message):
        return actual_decorator(message)
    return actual_decorator

def require_overseer(message=None):
    """Decorate a function to require the triggering user to be a FuelRats netadmin (as in, a highly ranked admin.).
    If they are not, `message` will be said if given."""
    def actual_decorator(function):
        @functools.wraps(function)
        def guarded(bot, trigger, *args, **kwargs):
            if getPrivLevel(trigger)<3:
                if message and not callable(message):
                    bot.say(message)
            else:
                return function(bot, trigger, *args, **kwargs)
        return guarded
    # Hack to allow decorator without parens
    if callable(message):
        return actual_decorator(message)
    return actual_decorator

def require_dispatch(message=None):
    """Decorate a function to require the triggering user to be a FuelRats netadmin (as in, a highly ranked admin.).
    If they are not, `message` will be said if given."""
    def actual_decorator(function):
        @functools.wraps(function)
        def guarded(bot, trigger, *args, **kwargs):
            if getPrivLevel(trigger)<2:
                if message and not callable(message):
                    bot.say(message)
            else:
                return function(bot, trigger, *args, **kwargs)
        return guarded
    # Hack to allow decorator without parens
    if callable(message):
        return actual_decorator(message)
    return actual_decorator

def require_rat(message=None):
    """Decorate a function to require the triggering user to be a FuelRats netadmin (as in, a highly ranked admin.).
    If they are not, `message` will be said if given."""
    def actual_decorator(function):
        @functools.wraps(function)
        def guarded(bot, trigger, *args, **kwargs):
            if getPrivLevel(trigger)<1:
                if message and not callable(message):
                    bot.say(message)
            else:
                return function(bot, trigger, *args, **kwargs)
        return guarded
    # Hack to allow decorator without parens
    if callable(message):
        return actual_decorator(message)
    return actual_decorator

def require_recruit(message=None):
    """Decorate a function to require the triggering user to be a FuelRats netadmin (as in, a highly ranked admin.).
    If they are not, `message` will be said if given."""
    def actual_decorator(function):
        @functools.wraps(function)
        def guarded(bot, trigger, *args, **kwargs):
            if getPrivLevel(trigger)<0:
                if message and not callable(message):
                    bot.say(message)
            else:
                return function(bot, trigger, *args, **kwargs)
        return guarded
    # Hack to allow decorator without parens
    if callable(message):
        return actual_decorator(message)
    return actual_decorator

privlevels = {'recruit.fuelrats.com':0, 'rat.fuelrats.com':1, 'dispatch.fuelrats.com':2, 'overseer.fuelrats.com':3, 'op.fuelrats.com':4, 'techrat.fuelrats.com':5, 'netadmin.fuelrats.com':6}

def getPrivLevel(trigger):
    print('getting priv level for '+str(trigger.nick)+' - host is: '+str(trigger.host))
    if trigger.owner:
        print('is owner. Returning 9.')
        return 9
    if trigger.admin:
        print('is admin. returning 8.')
        return 8
    else:
        if str(trigger.host) in privlevels.keys():
            level = privlevels.get(str(trigger.host))
            print('returning '+str(level))
            return level
        else:
            print('not in keys. Returning -1.')
            return -1