from PyQt4.QtCore import Qt, pyqtSignal
from PyQt4.QtGui import QApplication, QMainWindow, QStandardItemModel, QStandardItem, QTreeView, QDockWidget
from dataserver import resolve_path
from pyqt_utils.plot_widgets import CloseableDock, CrosshairPlotWidget, CrossSectionImageView, MPLPlotWidget, \
    BackendSwitchablePlot, BackendSwitchableDock, BackendSwitchableImageView
from pyqtgraph.dockarea import DockArea


class DataItem(QStandardItem):
    name = None
    datasrv = None
    def __init__(self, name):
        super(DataItem, self).__init__("")
        self.name = name
        self.setEditable(False)

    def path(self):
        if self.parent() is None:
            return self.name
        else:
            return self.parent().path() + "/" + self.name

    def get_proxy(self):
        fn, path = self.path().split("/", 1)
        file_proxy = datasrv.get_file(fn)
        return resolve_path(file_proxy, path)


class DataGroupItem(DataItem):
    def __init__(self, name, tree):
        super(DataGroupItem, self).__init__(name)
        for k, v in tree.items():
            if isinstance(v, dict):
                child = DataGroupItem(k, v)
            else:
                child = DataSetItem(k, v)
            self.appendRow(child)
        self.update_text()

    def update_text(self):
        if self.rowCount() == 0:
            child_str = "Empty"
        if self.rowCount() == 1:
            child_str = "1 child"
        else:
            child_str = "%d children" % self.rowCount()
        self.setText("%s (%s)" % (self.name, child_str))

class DataSetItem(DataItem):
    def __init__(self, name, shape):
        super(DataSetItem, self).__init__(name)
        self.shape = shape
        self.update_text()

    def update_text(self):
        self.setText("%s %s" % (self.name, self.shape))

class DataserverTreeView(QTreeView):
    dataset_activated = pyqtSignal('QStandardItem')
    def __init__(self, datasrv):
        super(DataserverTreeView, self).__init__()
        self.datasrv = datasrv
        self.tree_model = QStandardItemModel()
        self.setModel(self.tree_model)
        for fn, tree in datasrv.get_tree().items():
            self.tree_model.appendRow(DataGroupItem(fn, tree))
        self.doubleClicked.connect(self.index_activated)

    def index_activated(self, index):
        item = self.tree_model.itemFromIndex(index)
        if isinstance(item, DataSetItem):
            self.dataset_activated.emit(item)

class MainWindow(QMainWindow):
    def __init__(self, datasrv):
        super(MainWindow, self).__init__()
        self.datasrv = datasrv
        self.tree_dock = QDockWidget("Dataserver Browser")
        self.tree_widget = DataserverTreeView(datasrv)
        self.tree_widget.dataset_activated.connect(self.plot_item)
        self.tree_dock.setWidget(self.tree_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tree_dock)
        self.plot_dock_widget = DockArea()
        self.setCentralWidget(self.plot_dock_widget)

    def plot_item(self, i):
        data = i.get_proxy()[:]
        if len(data.shape) == 1:
            p = BackendSwitchablePlot()
        else:
            p = BackendSwitchableImageView()
        p.set_data(data)
        d = BackendSwitchableDock(i.name, widget=p)
        self.plot_dock_widget.addDock(d)


if __name__ == '__main__':
    import objectsharer
    objectsharer.backend.start_server('127.0.0.1')
    objectsharer.backend.connect_to('tcp://127.0.0.1:55556')
    datasrv = objectsharer.find_object('dataserver')
    print datasrv.get_file('test.h5')
    app = QApplication([])
    win = MainWindow(datasrv)
    win.show()
    app.exec_()
