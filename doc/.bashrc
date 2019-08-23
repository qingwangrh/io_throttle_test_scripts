# .bashrc

# User specific aliases and functions

alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi
alias wtree='tree --charset ASCII'
alias ll='ls -la'
alias ls='ls --color=auto'
alias findp='ps  aux|grep'
alias lsd="ls -d */|sed 's/\// /g'|xargs ls -d --color"
alias lsf="ls -p|grep [^/]$|xargs ls -lh --color"
#alias lsd="ls -d */|sed 's/\///g'"
alias wfind='find ./ -not \( -name .svn -a -prune \) -name'
alias wssh='ssh -o StrictHostKeyChecking=no '

if [[ -f /usr/bin/vim ]]; then
    alias vi=vim
fi

GREPCOL=""
if uname -a | grep sparc; then
    function sgrep {
        grep -n "$*" * | grep -v '\.svn/' | grep "$*"
    }

    export TERM=xterm-color
else
    GREPCOL=--color=auto
    function sgrep {
        echo $*
        grep -r -n -i "$*" ./ | grep -v '\.svn/' | grep --color=auto -i "$*"
    }

    if grep --help > /dev/null | grep "exclude-dir"; then
        GREP_OPTIONS="--exclude-dir=\.svn"
        export GREP_OPTIONS
    fi

fi


PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\] \[\033[01;33m\]\w\[\033[00m\] \$ '
PROMPT_COMMAND='echo -ne "\033]0;${HOSTNAME%%.*}  \007"'
wvnc() {
    if [ "x$1" = "x" ]; then
        VNC_ID=86
    else
        VNC_ID=$1
    fi
    if [ "x$2" = "x" ]; then
        VNC_RES=1600x1000
    else
        VNC_RES=$2
    fi
    cmd="vncserver -kill :${VNC_ID};  vncserver :${VNC_ID} -SecurityTypes None -geometry ${VNC_RES}"
    echo "$cmd"
    eval $cmd
}

wremote(){
	host=ibm
	port=$1
	if (($#>1));then
		host=$1
		port=$2

	fi
	cmd="remote-viewer vnc://$host:$port"
	echo "$cmd"
	${cmd}

}
wcp(){
	target=$1
	scp .bashrc $target:~/
       	scp /etc/hosts $target:/etc/hosts	
}

wloop() {
    echo "wloop start end action"
    unset n
    start=$1
    let end=$1+$2
    shift
    shift
    cmd="$@"
    for (( n = $start; n < $end; n ++ ))
    do
        echo ""
        echo "`date`- - - - - - - - - - -$n"
        #replace @@ with index
        new_cmd="${cmd//@@/$n}"
        echo -e "$new_cmd\n"
        #/bin/sh -c "$new_cmd"
	eval "$new_cmd"
    done
}

wloopl()
{

    unset n
    f=$1
    shift

    cmd="$@"
    if [[ "x$cmd" == "x" ]]; then
        return
    fi

    data=$(cat ${f})
    echo "$data"
    for n in $data
    do
        echo "- - - - - - - - - - -$n"
        new_cmd="${cmd//@@/$n}"
        echo "$new_cmd"
    done

}
wmount()
{
echo "mount.glusterfs gluster-virt-qe-01.lab.eng.pek2.redhat.com:/vol  /mnt/gluster"
echo "mount 10.73.194.27:/vol/s2kvmauto/iso  /mnt"
}
export PATH=$PATH:/usr/local/bin
export VTE="./var/lib/avocado/data/avocado-vt/backends/qemu/cfg/tests-example.cfg"

cd
#ulimit -c unlimited
