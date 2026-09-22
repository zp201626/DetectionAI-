# Detection 异常初筛 SOP

当 defect density 超过基线 2 倍，或 defect map 出现连续 edge ring、cluster 等空间模式时，应先对 lot 执行 hold，并确认复测结果是否可重复。

排查顺序建议为：检测设备状态（illumination、focus、alignment、stage）、recipe 最近变更、同机台相邻 lot、同层别跨机台对比，最后再判断是否为真实工艺异常。

如果 SPC 出现连续上升趋势并越过 UCL，应按特殊原因信号处理，不应直接放宽控制界限。需要保留原始 control chart、报警时间线、recipe 版本和 operator 信息。
