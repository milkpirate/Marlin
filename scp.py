Import("env")


def scp(source, target, env):
    local_file = source[0]
    remote = env.Dump("UPLOAD_PORT")

    scp_cmd = "scp {local} {remote}".format(
        local=local_file,
        remote=remote,
    )
    env.Execute(scp_cmd)


env.Replace(UPLOADCMD=scp)
