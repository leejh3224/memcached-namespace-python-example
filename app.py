from flask import Flask
import memcache
from datetime import datetime

mc = memcache.Client(['127.0.0.1:11211'], debug=0)

app = Flask(__name__)

def get_or_create_user_ns():
    key = 'ns:user'
    user_ns = mc.get(key)

    # server restarted, key evicted, etc...
    if not user_ns:
        new_ns_value = int(datetime.now().timestamp())
        mc.set(key, new_ns_value)
        return mc.get(key)
    return user_ns

def invalidate_user_ns():
    key = 'ns:user'
    new_ns_value = int(datetime.now().timestamp())
    mc.set(key, new_ns_value)

# Invalidates current user namespace
# NOTE it doesn't delete existing keys under old user namespace
# it simply makes old keys unreachable by applications
@app.route('/user_ns/invalidate', methods = ['POST'])
def user_ns_invalidate():
    invalidate_user_ns()
    new_user_ns = get_or_create_user_ns()
    return f'user_ns invalidated, new_user_ns is "{new_user_ns}"'

# Returns current user namespace
@app.route('/user_ns', methods = ['GET'])
def get_ns():
    user_ns = get_or_create_user_ns()
    return f'current user namespace value is "{str(user_ns)}"'

# Sets user cache
@app.route('/user/<user_id>', methods = ['POST'])
def set_user_cache(user_id):
    user_ns = get_or_create_user_ns()
    mc.set(f'{user_ns}:user:{user_id}', int(user_id))
    return 'ok'

# Returns user cache
@app.route('/user/<user_id>', methods = ['GET'])
def get_user_cache(user_id):
    user_ns = get_or_create_user_ns()
    value = mc.get(f'{user_ns}:user:{user_id}')
    return str(value)

"""
Testing namespace demo
1. Try getting user cache: GET localhost:5000/user/1234
2. 1. should return None
3. Set cache for user 1234: POST localhost:5000/user/1234
4. Try getting user cache again for user_id 1234
5. 4. should return 1234 as expected
6. Invalidate current user caches: POST localhost:5000/user_ns/invalidate
7. Try getting user cache again for user_id 1234
8. 7. should return None as all caches under user namespace are invalidated
"""
if __name__ == '__main__':
   app.run()
