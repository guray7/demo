import streamlit as st
import pandas as pd
import json
from datetime import datetime
import io

st.title("🛠️ .xer to Gantt JSON Converter")

uploaded_file = st.file_uploader("📂 Upload your .xer file", type=["xer"])

if uploaded_file:
    lines = uploaded_file.read().decode(errors="ignore").splitlines()

   #!/usr/bin/env python3
import json
import sys
from datetime import datetime
from dateutil import parser
import pytz
from typing import Dict, List, Any

class XerParser:
    def __init__(self, xer_file_path: str):
        self.xer_file_path = xer_file_path
        self.tables: Dict[str, List[Dict[str, Any]]] = {}
        self.current_table = None
        self.current_fields = []
        
    def parse(self) -> Dict[str, List[Dict[str, Any]]]:
        """Parse the XER file and return a dictionary of tables."""
        # Try different encodings
        encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(self.xer_file_path, 'r', encoding=encoding) as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                            
                        if line.startswith('%T'):
                            # New table definition
                            self.current_table = line[2:].strip()
                            self.tables[self.current_table] = []
                            self.current_fields = []
                        elif line.startswith('%F'):
                            # Field definitions
                            self.current_fields = line[2:].strip().split('\t')
                        elif line.startswith('%R'):
                            # Table row data
                            if self.current_table and self.current_fields:
                                values = line[2:].strip().split('\t')
                                row_dict = dict(zip(self.current_fields, values))
                                self.tables[self.current_table].append(row_dict)
                return self.tables
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error with encoding {encoding}: {str(e)}")
                continue
        
        raise Exception("Could not read file with any of the attempted encodings")

class GanttConverter:
    def __init__(self, tables: Dict[str, List[Dict[str, Any]]]):
        self.tables = tables
        self.tasks = []
        self.links = []
        self.link_counter = 1  # For numeric link IDs
        
    def convert(self) -> Dict[str, List[Dict[str, Any]]]:
        """Convert XER tables to dhtmlx Gantt format."""
        self._process_wbs()   # Add WBS/folder nodes first
        self._process_tasks() # Add activities as children of WBS
        self._process_links()
        return {
            "data": self.tasks,
            "links": self.links
        }
    
    def _process_wbs(self):
        """Process WBS table and add as folder/project nodes."""
        if 'WBS' not in self.tables:
            return
        for wbs in self.tables['WBS']:
            wbs_id = wbs.get('wbs_id', '')
            parent_wbs_id = wbs.get('parent_wbs_id', '') or "0"
            wbs_name = wbs.get('wbs_name', '')
            gantt_wbs = {
                "id": wbs_id,
                "text": wbs_name,
                "type": "project",
                "parent": parent_wbs_id if parent_wbs_id != wbs_id else "0",
                "wbs_id": wbs_id,
                "custom_fields": {}
            }
            self.tasks.append(gantt_wbs)
    
    def _process_tasks(self):
        """Process TASK table and convert to dhtmlx Gantt tasks."""
        if 'TASK' not in self.tables:
            return
        for task in self.tables['TASK']:
            # Use Primavera's original/remaining/float fields (in hours, convert to days)
            orig_dur = self._safe_float(task.get('orig_duration_hr_cnt', 0)) / 8.0
            remain_dur = self._safe_float(task.get('remain_duration_hr_cnt', 0)) / 8.0
            total_float = self._safe_float(task.get('total_float_hr_cnt', 0)) / 8.0
            # Calculate duration in days (fallback to original if missing)
            duration = orig_dur if orig_dur > 0 else self._calculate_duration(task)
            # Check if task is a milestone
            is_milestone = (task.get('task_type', '').upper() == 'ME' or duration == 0)
            # Get finish date
            finish_date = self._format_date(task.get('target_end_date', ''))
            # Get schedule percent complete
            schedule_percent = self._calculate_schedule_percent(task)
            # Progress: use physical if available, else schedule
            progress = self._calculate_progress(task)
            # Use WBS as parent
            parent = task.get('wbs_id', '')
            gantt_task = {
                "id": task.get('task_id', ''),
                "text": task.get('task_name', ''),
                "start_date": self._format_date(task.get('target_start_date', '')),
                "duration": duration,
                "progress": progress,
                "parent": parent,
                "type": "milestone" if is_milestone else "task",
                "wbs_id": parent,
                "custom_fields": {
                    "original_duration": orig_dur,
                    "remaining_duration": remain_dur,
                    "schedule_percent_complete": f"{schedule_percent}%",
                    "total_float": total_float,
                    "finish_date": finish_date,
                    "primavera_activity_id": task.get('task_code', '')
                }
            }
            self.tasks.append(gantt_task)
    
    def _process_links(self):
        """Process TASKPRED table and convert to dhtmlx Gantt links."""
        if 'TASKPRED' not in self.tables:
            return
        for pred in self.tables['TASKPRED']:
            link = {
                "id": self.link_counter,  # Numeric ID
                "source": pred.get('pred_task_id', ''),
                "target": pred.get('task_id', ''),
                "type": "0"  # Finish to Start
            }
            self.links.append(link)
            self.link_counter += 1
    
    def _format_date(self, date_str: str) -> str:
        """Convert XER date format to dhtmlx Gantt format (YYYY-MM-DD)."""
        if not date_str:
            return ""
        try:
            # Parse the date string and ensure it's in UTC
            dt = parser.parse(date_str)
            if dt.tzinfo is None:
                # If no timezone info, assume UTC
                dt = dt.replace(tzinfo=pytz.UTC)
            # Convert to local timezone if needed
            local_tz = pytz.timezone('UTC')  # You can change this to your local timezone if needed
            dt = dt.astimezone(local_tz)
            return dt.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"Error parsing date {date_str}: {str(e)}")
            return ""
    
    def _calculate_duration(self, task: Dict[str, Any]) -> float:
        """Calculate task duration in days."""
        try:
            # Parse start and end dates with timezone handling
            start = parser.parse(task.get('target_start_date', ''))
            end = parser.parse(task.get('target_end_date', ''))
            
            # Ensure both dates have timezone info
            if start.tzinfo is None:
                start = start.replace(tzinfo=pytz.UTC)
            if end.tzinfo is None:
                end = end.replace(tzinfo=pytz.UTC)
                
            # Calculate duration in days, rounding up to nearest day
            duration = (end - start).total_seconds() / (24 * 3600)
            return max(1, round(duration))  # Ensure minimum duration of 1 day
        except Exception as e:
            print(f"Error calculating duration: {str(e)}")
            return 1  # Default to 1 day if calculation fails
    
    def _calculate_schedule_percent(self, task: Dict[str, Any]) -> float:
        """Calculate schedule percent complete."""
        try:
            return float(task.get('sched_percent_complete', 0))
        except:
            return 0
    
    def _calculate_progress(self, task: Dict[str, Any]) -> float:
        """Calculate task progress percentage."""
        try:
            # Try to get physical percent complete first
            progress = float(task.get('phys_complete_pct', 0))
            if progress == 0:
                # Fall back to schedule percent complete if physical is 0
                progress = float(task.get('sched_percent_complete', 0))
            return progress / 100
        except:
            return 0

    def _safe_float(self, value):
        try:
            return float(value)
        except:
            return 0

def main():
    if len(sys.argv) != 3:
        print("Usage: python xer_to_gantt.py input.xer output.json")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        # Parse XER file
        parser = XerParser(input_file)
        tables = parser.parse()
        
        # Convert to Gantt format
        converter = GanttConverter(tables)
        gantt_data = converter.convert()
        
        # Write output
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(gantt_data, f, indent=2)
            
        print(f"Successfully converted {input_file} to {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
