def mylog(some_var):
    f = open("mylog.txt", "a")
    f.write("var = " + repr(some_var) + "\n")
    f.close
