%% ----------------- IMPORT LAP DATA -----------------

file1 = 'CS4_hotlap.csv';
file2 = 'NominalB_hotlap.csv';
setup1 = readtable(file1);
setup2 = readtable(file2);

s1_end = 1200;
s2_end = 2500;
s3_end = 4657;

[~, name1, ~] = fileparts(file1);
[~, name2, ~] = fileparts(file2);
name1 = strrep(name1, '_', '\_');
name2 = strrep(name2, '_', '\_');

darkGreen = [0 0.5 0];
lap_min = min([setup1.LapDistance_m; setup2.LapDistance_m]);
lap_max = max([setup1.LapDistance_m; setup2.LapDistance_m]);

%% ----------------- SPEED TRACE COMPARISON -----------------

figure('Name','Speed Trace Comparison','NumberTitle','off');
p1 = plot(setup1.LapDistance_m, setup1.Speed_km_h, 'Color', darkGreen, 'LineWidth', 1.5); hold on
p2 = plot(setup2.LapDistance_m, setup2.Speed_km_h, '-r', 'LineWidth', 1.5);
x1 = xline(s1_end, 'b--', 'S1 End', 'LabelOrientation', 'horizontal', 'LabelVerticalAlignment', 'bottom');
x2 = xline(s2_end, 'c--', 'S2 End', 'LabelOrientation', 'horizontal', 'LabelVerticalAlignment', 'bottom');
x3 = xline(s3_end, 'm--', 'S3 End', 'LabelOrientation', 'horizontal', 'LabelVerticalAlignment', 'bottom');
xlabel('Lap Distance (m)');
ylabel('Speed (km/h)');
title('Comparison of Hot‐Lap Speed');
grid on
xlim([lap_min, lap_max]);
legend([p1, p2, x1, x2, x3], {name1, name2, 'S1 End', 'S2 End', 'S3 End'}, 'Location','best');

%% ----------------- THROTTLE POSITION COMPARISON -----------------

figure('Name','Throttle Position Comparison','NumberTitle','off');
p1 = plot(setup1.LapDistance_m, setup1.Throttle_pct, 'Color', darkGreen, 'LineWidth', 1.5); hold on
p2 = plot(setup2.LapDistance_m, setup2.Throttle_pct, '-r', 'LineWidth', 1.5);
x1 = xline(s1_end, 'b--');
x2 = xline(s2_end, 'c--');
x3 = xline(s3_end, 'm--');
xlabel('Lap Distance (m)');
ylabel('Throttle (%)');
title('Comparison of Throttle Position');
grid on
xlim([lap_min, lap_max]);
legend([p1, p2, x1, x2, x3], {name1, name2, 'S1 End', 'S2 End', 'S3 End'}, 'Location','best');

%% ----------------- BRAKE POSITION COMPARISON -----------------

figure('Name','Brake Position Comparison','NumberTitle','off');
p1 = plot(setup1.LapDistance_m, setup1.Brake_pct, 'Color', darkGreen, 'LineWidth', 1.5); hold on
p2 = plot(setup2.LapDistance_m, setup2.Brake_pct, '-r', 'LineWidth', 1.5);
x1 = xline(s1_end, 'b--');
x2 = xline(s2_end, 'c--');
x3 = xline(s3_end, 'm--');
xlabel('Lap Distance (m)');
ylabel('Brake (%)');
title('Comparison of Brake Position');
grid on
xlim([lap_min, lap_max]);
legend([p1, p2, x1, x2, x3], {name1, name2, 'S1 End', 'S2 End', 'S3 End'}, 'Location','best');

%% ----------------- GEAR COMPARISON -----------------

figure('Name','Gear Comparison','NumberTitle','off');
p1 = plot(setup1.LapDistance_m, setup1.Gear, 'Color', darkGreen, 'LineWidth', 1.5); hold on
p2 = plot(setup2.LapDistance_m, setup2.Gear, '-r', 'LineWidth', 1.5);
x1 = xline(s1_end, 'b--');
x2 = xline(s2_end, 'c--');
x3 = xline(s3_end, 'm--');
xlabel('Lap Distance (m)');
ylabel('Gear');
title('Comparison of Gear Selection');
grid on
xlim([lap_min, lap_max]);
legend([p1, p2, x1, x2, x3], {name1, name2, 'S1 End', 'S2 End', 'S3 End'}, 'Location','best');

%% ----------------- STEERING ANGLE COMPARISON -----------------

figure('Name','Steering Angle Comparison','NumberTitle','off');
p1 = plot(setup1.LapDistance_m, setup1.Steering_deg, 'Color', darkGreen, 'LineWidth', 1.5); hold on
p2 = plot(setup2.LapDistance_m, setup2.Steering_deg, '-r', 'LineWidth', 1.5);
x1 = xline(s1_end, 'b--');
x2 = xline(s2_end, 'c--');
x3 = xline(s3_end, 'm--');
xlabel('Lap Distance (m)');
ylabel('Steering Angle (°)');
title('Comparison of Steering Angle');
grid on
xlim([lap_min, lap_max]);
legend([p1, p2, x1, x2, x3], {name1, name2, 'S1 End', 'S2 End', 'S3 End'}, 'Location','best');

%% ----------------- LAP TIME vs LAP DISTANCE -----------------

% Convert speed from km/h to m/s
setup1.Speed_m_s = setup1.Speed_km_h / 3.6;
setup2.Speed_m_s = setup2.Speed_km_h / 3.6;

% Compute delta distance between consecutive points
delta_s1 = [0; diff(setup1.LapDistance_m)]; % first segment 0
delta_s2 = [0; diff(setup2.LapDistance_m)];

% Compute delta time for each segment: dt = ds / v
dt1 = delta_s1 ./ setup1.Speed_m_s;
dt2 = delta_s2 ./ setup2.Speed_m_s;

% Cumulative lap time in seconds
lapTime1 = cumsum(dt1);
lapTime2 = cumsum(dt2);

% Plot Lap Time vs Lap Distance
figure('Name','Lap Time vs Lap Distance','NumberTitle','off');
p1 = plot(setup1.LapDistance_m, lapTime1, 'Color', darkGreen, 'LineWidth', 1.5); hold on
p2 = plot(setup2.LapDistance_m, lapTime2, '-r', 'LineWidth', 1.5);
x1 = xline(s1_end, 'b--', 'S1 End', 'LabelOrientation', 'horizontal', 'LabelVerticalAlignment', 'bottom');
x2 = xline(s2_end, 'c--', 'S2 End', 'LabelOrientation', 'horizontal', 'LabelVerticalAlignment', 'bottom');
x3 = xline(s3_end, 'm--', 'S3 End', 'LabelOrientation', 'horizontal', 'LabelVerticalAlignment', 'bottom');
xlabel('Lap Distance (m)');
ylabel('Cumulative Lap Time (s)');
title('Lap Time vs Lap Distance');
grid on
xlim([lap_min, lap_max]);
legend([p1, p2, x1, x2, x3], {name1, name2, 'S1 End', 'S2 End', 'S3 End'}, 'Location','best');
