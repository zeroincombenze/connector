[[ ! -d $HOME/tmp ]] && mkdir $HOME/tmp
FCONF="/etc/odoo/odoo10.conf"
LCONF="/home/odoo/10.0/connector/universal_connector/tests/logs/zero10.connector.universal_connector.conf"
LGITMPL="$HOME/clodoo/confs/10-0.conf"
LGICNF="$HOME/tmp/odoorc"
PIDFILE="/var/run/odoo/odoo10_test.pid"
DB="connect10"
PYCMD="$(readlink -f $(dirname $0)/ext_test_synchro.py)"
OPTS="--no-conai --ask --no-module"
ODOO_DIR="$HOME/10.0"
VENV="$ODOO_DIR/venv_odoo"
COVERAGE_PROCESS_START="$HOME/tmp/connector10rc"
COVERAGE_DATA_FILE="$HOME/tmp/cover_connector10"
PKGPATH=$(readlink -f $(dirname $0)/../)
HOME_DEVEL=$(readlink -f $(dirname $0)/../../../../devel)
XPORT="63494"
# XPORT="8170"

# cp $LGITMPL $LGICNF
# sed -E "s|xmlrpc_port *=.*|xmlrpc_port=$XPORT|" -i $LGICNF
# cp $FCONF $LCONF
# sed -E "s|xmlrpc_port *=.*|xmlrpc_port=$XPORT|" -i $LCONF
# sed -E "s|pidfile *=.*|pidfile=$PIDFILE|" -i $LCONF
# sed -E "s|^workers *=.*|workers = 0|" -i $LCONF
# cp $HOME_DEVEL/pypi/zerobug/zerobug/_travis/cfg/coveragerc $COVERAGE_PROCESS_START
# grep -Eq "^data_file *=" $COVERAGE_PROCESS_START || sed -E "/^\[run\]/a\\\ndata_file=$COVERAGE_DATA_FILE\n" -i $COVERAGE_PROCESS_START
# sed -E "s|^ *\*.py|    $PKGPATH|" -i $COVERAGE_PROCESS_START

cd $VENV
. $VENV/bin/activate
cd $ODOO_DIR
# echo $ODOO_DIR/odoo-bin --config=$LCONF
# coverage run --rcfile=$COVERAGE_PROCESS_START $ODOO_DIR/odoo-bin --config=$LCONF &
# sleep 2
echo $VENV/bin/python $PYCMD $OPTS --dbname $DB --config $LGICNF
$VENV/bin/python $PYCMD $OPTS --dbname $DB --config $LGICNF
# pid=$(ps -ef | grep "$ODOO_DIR/odoo-bin.*$LCONF" | grep -v grep | grep -v coverage | awk '{print $2}' | head -n1)
# [[ -n $pid ]] && kill $pid && sleep 1
# pid=$(ps -ef | grep "$ODOO_DIR/odoo-bin.*$LCONF" | grep -v grep | awk '{print $2}' | head -n1)
# [[ -n $pid ]] && kill $pid && sleep 1
# coverage report --rcfile=$COVERAGE_PROCESS_START -im
deactivate
sleep 2
# ps -ef|grep "$ODOO_DIR/odoo-bin.*$LCONF"

