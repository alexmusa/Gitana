__author__ = 'valerio cosentino'

from gitana.gitana import Gitana

CONFIG = {
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'port': '3306',
            'raise_on_warnings': False,
            'buffered': True
        }


def _papyrus_export():
    g = Gitana(CONFIG)
    g.export_graph("_papyrus_db", "./graph.json", "./graph.gexf")
    g.export_activity_report("_papyrus_db", "./report.json", "./report.html")


def _cesiumjs_export():
    g = Gitana(CONFIG)
    g.export_graph("db_cesium", "./graph-cesium.json", "./graph-cesium.gexf")
    g.export_activity_report("db_cesium", "./report-cesium.json", "./report-cesium.html")


def _json_export():
    g = Gitana(CONFIG)
    g.export_json("db_2048", "repo_2048", "./file-dump.json", references=["origin/master"])


def main():
    _json_export()

if __name__ == "__main__":
    main()