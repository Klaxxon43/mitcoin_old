from untils.Imports import *

cache_lock = Lock()
chat_cache_lock = Lock()
post_cache_lock = Lock()
link_cache_lock = Lock()
boost_cache_lock = Lock()
reaction_cache_lock = Lock()

task_cache = {}
task_cache_chat = {}