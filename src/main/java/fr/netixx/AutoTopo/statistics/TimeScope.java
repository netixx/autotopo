package fr.netixx.AutoTopo.statistics;

import au.com.bytecode.opencsv.CSVWriter;
import fr.netixx.AutoTopo.agents.IScope;
import fr.netixx.AutoTopo.agents.Scope;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.OpenOption;
import java.nio.file.Path;
import java.util.Map;
import java.util.SortedMap;
import java.util.TreeMap;

public class TimeScope extends AbstractStatistic {

    private static boolean enabled = true;
    private static final String[] headers = new String[]{"scope", "create", "delete", "avg","std", "min", "max"};
    private SortedMap<IScope, ConnectionsRecorder> connectionMap = new TreeMap<>();

    private RecordFilter<IScope> filter = null;

    public TimeScope(String name) {
        super(name, headers);
    }

    public TimeScope(String name, RecordFilter<IScope> filter) {
        super(name, headers);
        this.filter = filter;
    }

    public void record(Double time, IScope el) {
        if (enabled) {
            if (filter != null && filter.filter(el))
                return;
            if (!connectionMap.containsKey(el)) {
                connectionMap.put(el, new ConnectionsRecorder(1, time));
            } else {
                connectionMap.get(el).recordConnectionNumber(1, time);
            }
        }

        // el.getConnectionManager().getConnectedChildren().size();
    }

    @Override
    public void toCsv(Path csv) {
        OpenOption[] opts = new OpenOption[]{
                // StandardOpenOption .WRITE, StandardOpenOption.CREATE
        };
        try (BufferedWriter writer = Files.newBufferedWriter(csv, Charset.forName("UTF-8"), opts)) {
            CSVWriter csvW = new CSVWriter(writer, ';');

            csvW.writeNext(this.getHeader());
            for (Map.Entry<IScope, ConnectionsRecorder> entry : connectionMap.entrySet()) {
                csvW.writeNext(new String[]{"" + entry.getKey().getId(),
                        "" + entry.getValue().createTime,
                        "" + entry.getValue().destroyTime,
                        "" + entry.getValue().getAvg(),
                        "" + entry.getValue().getStd(),
                        "" + entry.getValue().getMin(),
                        "" + entry.getValue().getMax()});
            }
            csvW.close();
        } catch (IOException e) {
            e.printStackTrace();
        }

    }

    private class ConnectionsRecorder {
        double createTime;
        double destroyTime;

        double currentTime;
        int curConn;

        int n = 0;
        int max = 0;
        int min = 0;
        double m = 0;
        double s = 0;


        ConnectionsRecorder(int nConnections, double time) {
            this.createTime = time;
            currentTime = time;
            curConn = 0;
            n = 1;
            max = nConnections;
            min = nConnections;
            recordConnectionNumber(nConnections, time);
        }

        void recordConnectionNumber(int nConnections, double time) {
            destroyTime = time;
            if (time == currentTime) {
                curConn += nConnections;
            } else {
                //start new
                max = Math.max(curConn, max);
                min = Math.min(curConn, min);
                double tmpM = m;
                m += (curConn - tmpM) / n;
                s += (curConn - tmpM) * (curConn - m);
                n++;
                curConn = nConnections;
            }
        }

        double getAvg() {
            return m;
        }

        double getVariance() {
            return s / (n - 1);
        }

        double getStd() {
            return Math.sqrt(getVariance());
        }

        int getMax() {
            return max;
        }

        int getMin() {
            return min;
        }

    }
}