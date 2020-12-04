def traceback_decorator(func):
    def wrapeer(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            import traceback
            traceback.print_exc()
            input('\n Press any key to continue...')
    return wrapeer
