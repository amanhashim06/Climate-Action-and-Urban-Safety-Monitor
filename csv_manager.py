import os
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"

MISSING_EXCLUDE = "Exclude rows with missing values"
MISSING_MEDIAN = "Fill missing numbers with the median"


class CSVManager:
    filename = ""
    id_column = "id"
    id_prefix = "R"
    columns = []
    fields = []
    duplicate_keys = []

    def __init__(self):
        self._path = DATA_DIR / self.filename
        self.warnings = []
        self._data = self._empty()

    @property
    def data(self):
        return self._data.copy()

    @property
    def path(self):
        return self._path

    def _names(self, *kinds):
        return [f["name"] for f in self.fields if f["kind"] in kinds]

    def _empty(self):
        return self.clean_types(pd.DataFrame(columns=self.columns))[0]

    def clean_types(self, df):
        df = df.copy()
        warnings = []
        special = set(self._names("float", "int", "date"))
        for col in self.columns:
            if col not in special:
                df[col] = df[col].fillna("").astype(str).str.strip()
        df[self.id_column] = df[self.id_column].str.upper()
        for field in self.fields:
            name, kind = field["name"], field["kind"]
            if kind in ("float", "int"):
                converted = pd.to_numeric(df[name], errors="coerce")
                bad = int((converted.isna() & df[name].notna()).sum())
                if bad:
                    warnings.append(f"{bad} value(s) in '{name}' are not numbers and were treated as missing.")
                df[name] = converted.round().astype("Int64") if kind == "int" else converted.astype(float)
            elif kind == "date":
                converted = pd.to_datetime(df[name], errors="coerce")
                bad = int((converted.isna() & df[name].notna()).sum())
                if bad:
                    warnings.append(f"{bad} value(s) in '{name}' are not valid dates and were treated as missing.")
                df[name] = converted
        return df, warnings

    def load(self):
        df = self._empty()
        self.warnings = []
        ok, message = True, f"Loaded {self.filename}."
        try:
            raw = pd.read_csv(self._path)
        except FileNotFoundError:
            ok, message = False, f"{self.filename} was not found in the data folder. Put the file back or add a first record to create it."
        except pd.errors.EmptyDataError:
            ok, message = False, f"{self.filename} is empty. Add a record or restore the file."
        except Exception as error:
            ok, message = False, f"Could not read {self.filename}: {error}"
        else:
            missing = [c for c in self.columns if c not in raw.columns]
            if missing:
                ok, message = False, f"{self.filename} is missing column(s): {', '.join(missing)}."
            else:
                df, self.warnings = self.clean_types(raw[self.columns])
                repeated = int(df[self.id_column].duplicated().sum())
                if repeated:
                    self.warnings.append(f"{repeated} repeated record ID(s) found in {self.filename}.")
        finally:
            self._data = df
        return ok, message

    def _for_disk(self, df):
        out = df[self.columns].copy()
        for name in self._names("date"):
            out[name] = out[name].dt.strftime("%Y-%m-%d")
        return out

    def save(self, df):
        tmp = self._path.with_suffix(".tmp")
        ok, message = True, "Saved."
        try:
            DATA_DIR.mkdir(exist_ok=True)
            self._for_disk(df).to_csv(tmp, index=False)
            os.replace(tmp, self._path)
        except PermissionError:
            ok, message = False, f"Could not save {self.filename}. Close it in other programs (like Excel) and try again."
        except Exception as error:
            ok, message = False, f"Could not save {self.filename}: {error}"
        else:
            message = f"Saved to {self.filename}."
        finally:
            if tmp.exists():
                tmp.unlink()
        return ok, message

    def ids(self):
        return self._data[self.id_column].tolist()

    def next_id(self):
        numbers = pd.to_numeric(self._data[self.id_column].str.extract(r"(\d+)$")[0], errors="coerce")
        number = int(numbers.max()) + 1 if numbers.notna().any() else 1
        return f"{self.id_prefix}{number:03d}"

    def get_record(self, record_id):
        record_id = str(record_id).strip().upper()
        match = self._data[self._data[self.id_column] == record_id]
        if match.empty:
            return None
        return match.iloc[0].to_dict()

    def validate(self, values):
        cleaned, errors = {}, []
        for field in self.fields:
            name, label, kind = field["name"], field["label"], field["kind"]
            raw = values.get(name)
            if kind in ("text", "select"):
                text = "" if raw is None else str(raw).strip()
                if not text:
                    errors.append(f"{label} is required.")
                    continue
                if kind == "select" and text not in field["options"]:
                    errors.append(f"{label} must be one of: {', '.join(field['options'])}.")
                    continue
                if len(text) > 60:
                    errors.append(f"{label} is too long (max 60 characters).")
                    continue
                cleaned[name] = text.title() if field.get("title") else text
            elif kind in ("float", "int"):
                if raw is None or str(raw).strip() == "":
                    errors.append(f"{label} is required.")
                    continue
                try:
                    number = float(raw)
                except (TypeError, ValueError):
                    errors.append(f"{label} must be a number.")
                    continue
                if number != number or number in (float("inf"), float("-inf")):
                    errors.append(f"{label} must be a real number.")
                    continue
                if kind == "int" and number != int(number):
                    errors.append(f"{label} must be a whole number.")
                    continue
                low, high = field.get("min"), field.get("max")
                if (low is not None and number < low) or (high is not None and number > high):
                    errors.append(f"{label} must be between {low} and {high}.")
                    continue
                cleaned[name] = int(number) if kind == "int" else number
            elif kind == "date":
                try:
                    cleaned[name] = pd.Timestamp(raw).normalize()
                except (TypeError, ValueError):
                    errors.append(f"{label} must be a valid date.")
        return cleaned, errors

    def prepare(self, cleaned):
        return cleaned

    def find_duplicate(self, cleaned, ignore_id=None):
        if not self.duplicate_keys or len(self._data) == 0:
            return False
        df = self._data
        if ignore_id:
            df = df[df[self.id_column] != ignore_id]
        mask = pd.Series(True, index=df.index)
        for key in self.duplicate_keys:
            if key in self._names("date"):
                mask &= df[key] == cleaned[key]
            else:
                mask &= df[key].astype(str).str.lower() == str(cleaned[key]).lower()
        return bool(mask.any())

    def duplicate_message(self):
        return "A record with the same " + " + ".join(self.duplicate_keys) + " already exists."

    def add_record(self, record_id, values):
        record_id = str(record_id).strip().upper()
        if not record_id or " " in record_id:
            return False, "Record ID is required and cannot contain spaces."
        if record_id in self.ids():
            return False, f"Record ID {record_id} already exists. Use a different ID."
        cleaned, errors = self.validate(values)
        if errors:
            return False, "Please fix these problems:\n" + "\n".join(f"- {e}" for e in errors)
        if self.find_duplicate(cleaned):
            return False, self.duplicate_message()
        row = {self.id_column: record_id, **self.prepare(cleaned)}
        new_row = pd.DataFrame([row])
        combined = new_row if self._data.empty else pd.concat([self._data, new_row], ignore_index=True)
        combined = self.clean_types(combined)[0]
        ok, message = self.save(combined)
        if ok:
            self._data = combined
            message = f"Record {record_id} added. " + message
        return ok, message

    def update_record(self, record_id, values):
        record_id = str(record_id).strip().upper()
        if record_id not in self.ids():
            return False, f"Record ID {record_id or '(blank)'} was not found."
        cleaned, errors = self.validate(values)
        if errors:
            return False, "Please fix these problems:\n" + "\n".join(f"- {e}" for e in errors)
        if self.find_duplicate(cleaned, ignore_id=record_id):
            return False, self.duplicate_message()
        updated = self._data.copy()
        index = updated.index[updated[self.id_column] == record_id][0]
        for name, value in self.prepare(cleaned).items():
            updated.at[index, name] = value
        updated = self.clean_types(updated)[0]
        ok, message = self.save(updated)
        if ok:
            self._data = updated
            message = f"Record {record_id} updated. " + message
        return ok, message

    def delete_record(self, record_id):
        record_id = str(record_id).strip().upper()
        if record_id not in self.ids():
            return False, f"Record ID {record_id or '(blank)'} was not found."
        remaining = self._data[self._data[self.id_column] != record_id].reset_index(drop=True)
        ok, message = self.save(remaining)
        if ok:
            self._data = remaining
            message = f"Record {record_id} deleted. " + message
        return ok, message

    def missing_count(self, df):
        columns = self._names("float", "int", "date")
        return int(df[columns].isna().any(axis=1).sum())

    def handle_missing(self, df, mode):
        numbers = self._names("float", "int")
        dates = self._names("date")
        if mode == MISSING_MEDIAN:
            df = df.copy()
            for field in self.fields:
                name = field["name"]
                if name in numbers:
                    median = df[name].median()
                    if pd.notna(median):
                        df[name] = df[name].fillna(round(median) if field["kind"] == "int" else median)
            return df.dropna(subset=dates)
        return df.dropna(subset=numbers + dates)
