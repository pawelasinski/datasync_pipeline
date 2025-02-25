# DataSync Pipeline

This mini-project showcases how to use **Protobuf** and **FlatBuffers** for data serialization.

## Features

- Generation of synthetic server metrics (CPU, memory, disk).
- Data serialization in JSON, Protobuf, and FlatBuffers.
- Data transfer via gRPC.
- Comparison of file sizes and serialization/deserialization times.
- Graph generation using Matplotlib.
- _Logging of all operations to files and the console._
- _Error checking (server availability, data correctness)._

## Prerequisites

- Docker
- Docker Compose

## Installation and Execution

1. **Clone the repository**:
   ```bash
   git clone https://github.com/pawelasinski/datasync_pipeline.git
   cd datasync_pipeline
   ```

2. **Run the project**:
   ```bash
   docker compose up --build --no-cache
   ```
   - The server will start on port `50051`.
   - The client will generate data and send it to the server.
   - The corresponding script will analyze the data and build graphs based on the analysis.

3. **Check the results**:
   - The `results/` folder will contain:
     - `metrics.json`, `metrics.proto.bin`, `metrics.flatbuf` — saved data.
     - `serialize_times.json`, `deserialize_times.json` — measurements of serialization/deserialization times.
     - `size_comparison.png`, `performance_comparison.png` — graphs.
     - `logs/client.log`, `logs/server.log`, `logs/analysis.log` — logs.

4. **Stop the containers**:
   ```bash
   docker compose down
   ```
   - To remove volumes as well, add the flag `--volumes`: `docker compose down --volumes`.

## Project File Structure

```text
datasync_pipeline/
├── client/                          # Client side
│   ├── Dockerfile                      # Dockerfile for the client
│   ├── client.py                       # Data generation and sending via gRPC
│   ├── data_generator.py               # Generation of synthetic metrics
│   └── serializers.py                  # Serialization logic (JSON, Protobuf, FlatBuffers)
├── server/                          # Server side
│   ├── Dockerfile                      # Dockerfile for the server
│   ├── server.py                       # gRPC server for receiving data
│   ├── storage.py                      # Saving data to files
│   └── deserialize_performance.py      # Measuring time and size
├── proto/                           # Protobuf schemas
│   └── metrics.proto                   # Schema for server metrics
├── flatbuffers_schema/              # FlatBuffers schemas
│   └── metrics.fbs                     # Schema for server metrics
├── analysis/                        # Results analysis
│   ├── Dockerfile                      # Dockerfile for the analysis
│   └── analyze.py                      # Comparison and graph generation
├── results/                         # Folder for results (data files, graphs, and logs; will be mounted as a volume)
│   ├── logs/                           # Folder for logs (created automatically)
│   └── ...                             # Data files and graphs
├── README.md                        # Project description
├── docker-compose.yml               # File for managing all services
└── requirements.txt                 # Dependencies
```

## Example Logs

```
...
2025-02-22 10:00:01,123 - INFO - JSON deserialization took 0.0023 seconds, size: 128 bytes.
2025-02-22 10:00:01,124 - INFO - Protobuf deserialization took 0.0015 seconds, size: 64 bytes.
2025-02-22 10:00:01,125 - INFO - FlatBuffers deserialization took 0.0010 seconds, size: 80 bytes.
2025-02-22 10:00:01,126 - INFO - Processed 2 metrics in performance measurement.
...
```

## Possible Project Extensions

- Integrate real data instead of synthetic.
- Add support for other formats (e.g., Avro).
- ...

## License

[MIT License](./LICENSE)

## Author

Pawel Asinski (pawel.asinski@gmail.com)

---

## Protobuf vs. FlatBuffers

**Protobuf** (Protocol Buffers) and **FlatBuffers** are two binary data serialization formats developed by Google. They are used for efficient transmission of structured data and are suitable for a variety of scenarios: from microservices and IoT devices to game engines and mobile applications.

### Brief Overview

Protobuf focuses on the efficient serialization of structured data for network transmission (RPC, microservices, etc.), whereas FlatBuffers minimizes data copying (zero-copy) and provides fast direct access to data without pre-parsing.

### Format Structures

#### Protobuf

1. **Message definition** in `.proto` files:
   ```proto
   message Person {
       string name = 1;
       int32 age = 2;
   }
   ```
2. Data is encoded as a stream of bytes with **tags** (field number + type). Each field has a number (e.g., name = 1, age = 2), and a tag precedes the value to indicate: "This is field number 1, here is its data." This makes serialization compact and allows skipping unknown fields.
    ```text
    [0A 05 50 61 77 65 6C] [10 1C]
     field 1: "Pawel"   field 2: 28
    ```
   Here:
    - `0A` is the tag for the string (field 1).
    - `05` is the length of the string, followed by "Pawel".
    - `10` is the tag for the number (field 2).
    - `1C` represents 28.
3. Although the data is compact, it must be parsed upon reading: the program interprets the tags and values and creates objects in memory.

#### FlatBuffers

1. **Schema definition** in `.fbs` files:
   ```fbs
   table Person {
       name: string;
       age: int;
   }
   ```
2. Data is written into a "flat" buffer (all data is stored in one continuous sequence of bytes—like a long tape where everything follows in order) along with a table of pointers (offsets). There are no tags before each value; instead, a table at the beginning indicates where each value is located.
    ```text
    [04 00 00 00] [08 00] [0C 00] [05 00 00 00] [50 61 77 65 6C] [1C 00 00 00]
     header bytes      table      string length    "Pawel" string   age
    ```
   Here:
    - Data:
        - The string "Pawel":
            - String length: 5 bytes (for "Pawel"), recorded as a 4-byte integer: `05 00 00 00`.
            - Characters: bytes for "P", "a", "w", "e", "l" in UTF-8: `50 61 77 65 6C`.
        - The number 28 (int): occupies 4 bytes, in hex this is `1C 00 00 00` (28 in decimal).
    - Pointer table (offsets in bytes from the start of the table to the data):
        - `08 00` — an offset of 8 bytes from the start of the table to the string "Pawel".
        - `0C 00` — an offset of 12 bytes to the age.
    - At the beginning of the buffer, header bytes indicate the start of the table (for example, its position):
        - `04 00 00 00` — offset to the table.

3. The data is already in memory in a ready-to-use format (zero-copy), allowing direct reading by following pointers without the need for full parsing.

---

### Advantages and Disadvantages

#### Protobuf

**Advantages**:

1. A mature ecosystem with numerous tools and libraries (native gRPC support).
2. Wide language support (C++, Python, Java, etc.), making it suitable for projects that involve multiple languages.
3. Easy schema evolution: new fields can be added with new tags while older code ignores them.
4. Compact binary format, especially efficient compared to XML/JSON.

**Disadvantages**:

1. Requires a compilation step for `.proto` files into code.
2. Accessing fields necessitates parsing the entire message.
3. While memory savings are better than text formats, FlatBuffers can be even more efficient in certain scenarios.

#### FlatBuffers

**Advantages**:

1. Zero-copy deserialization: direct access to specific fields in the buffer without parsing the entire message.
2. Efficient memory usage (especially beneficial in resource-constrained environments like mobile devices and games).
3. High-speed data access (particularly when frequently accessing elements).
4. Support for a simple JSON format for debugging (the `flatc` compiler can convert between FlatBuffers and JSON).
5. Wide language support (C++, Python, Rust, TypeScript, etc.).

**Disadvantages**:

1. A less mature ecosystem compared to Protobuf, with fewer community resources.
2. More complex to learn, especially when working directly with the buffer.
3. Schema evolution rules are stricter: field order cannot be changed, and fields can only be marked as `deprecated` rather than removed.

---

### Schema Evolution

#### Protobuf

- **Adding new fields** (simply assign new numbers (e.g., `email = 3`)).
- **Reserving old fields** (use the `reserved` keyword to avoid conflicts).
- **Changing types** (requires caution—if the type is incompatible, a new field should be used).

#### FlatBuffers

- **Adding new fields** (must be appended strictly at the end of the table to maintain the binary structure).
- **Removing fields** (cannot be removed; they can only be marked as `deprecated` to preserve compatibility).
- **Changing numeric types** (changing types (e.g., from `int` to `long`) requires verifying compatibility to avoid conflicts in the binary schema).

---

### Python Examples

#### Protobuf

**Step 1.** Create the file `person.proto`:

```proto
// Define the serialization/deserialization rules. Without this line, proto2 is used by default, which may lead to unexpected behavior.
syntax = "proto3";

/*
 * The package "example" groups all messages in this file.
 * This prevents naming conflicts with other schemas.
 */
package example;

message Person {
    // The field "name" stores a person's name in UTF-8 format.
    string name = 1; // Default value is "", if not set.

    // The field "age" indicates the age as a 32-bit integer.
    int32 age = 2; // Default value is 0, if not set.
}
```

**Step 2.** Compile the `.proto` file into Python code (using [grpc-tools](https://pypi.org/project/grpcio-tools/)):

```bash
python -m grpc_tools.protoc -I. --python_out=. person.proto
```

This will generate the file `person_pb2.py`.

**Step 3.** Usage in Python code:

```python
import example.person_pb2 as person_pb2

# Create a Person message object.
# person_pb2.Person() is the constructor for the Person class defined in person.proto.
# It creates an empty object where the fields name and age have default values ("" and 0 for proto3).
msg = person_pb2.Person()
msg.name = "Pawel"
msg.age = 28

# Serialize to binary format (bytes).
# SerializeToString() converts the msg object into a byte sequence according to the Protobuf schema.
serialized_data = msg.SerializeToString()

# ParseFromString fills msg2 with data from serialized_data.
# The method parses the bytes, recognizes the tags (1 for name, 2 for age), and assigns values to msg2's fields.
msg2 = person_pb2.Person()
msg2.ParseFromString(serialized_data)

print("Person:", msg2.name)
print("Age:", msg2.age)
```

#### FlatBuffers

**Step 1.** Define the schema in the file `person.fbs`:

```fbs
// Define the namespace for the generated code to avoid naming conflicts, especially if you have multiple schemas. All objects from this schema will be placed in the Example module (e.g., Example/Person.py in Python).
namespace Example;

table Person {
    name: string;
    age: int;
}

/* 
    Specify that Person is the root type in the buffer. FlatBuffers requires knowing which object is the "entry point" in the buffer. This is needed for deserialization—so that GetRootAsPerson knows where to start.
*/
root_type Person;
```

**Step 2.** Compile the schema into Python code (using [flatc](https://github.com/google/flatbuffers)):

```bash
flatc --python person.fbs
```

Files will be generated, such as `Person.py` and the directory `Example` (depending on your version of `flatc`).

**Step 3.** Usage in Python code:

```python
import flatbuffers
import Example.Person as Person  # Import the generated module.

# Serialization.
# Create a Builder object — the primary tool for constructing a FlatBuffers buffer.
# initialSize=1024 sets the initial buffer size in bytes (1024 bytes) to avoid frequent memory reallocations.
builder = flatbuffers.Builder(initialSize=1024)

# Create a string offset (pointer) for the "name" field.
# The CreateString method writes the string "Pawel" into the buffer (including its length and UTF-8 bytes) and returns an offset indicating its location in the buffer.
name_offset = builder.CreateString("Pawel")

# Begin constructing the Person object in the buffer.
# PersonStart prepares a table for the Person object, allocating space for pointers to fields (name and age).
Person.PersonStart(builder)

# Add the name field to the Person table.
# PersonAddName takes the string offset (name_offset) that was created earlier and writes it into the table.
Person.PersonAddName(builder, name_offset)

# Add the age field to the Person table.
# PersonAddAge writes the number 28 directly (an int occupies 4 bytes) without creating a separate offset, as it is a primitive type.
Person.PersonAddAge(builder, 28)

# Finish constructing the Person object.
# PersonEnd finalizes the table, returning an offset to the beginning of this table in the buffer.
person_obj = Person.PersonEnd(builder)

# Complete the entire buffer.
# Finish tells the Builder that person_obj is the root object and adds header bytes at the beginning of the buffer (e.g., a pointer to the table).
builder.Finish(person_obj)

# Obtain the final binary buffer.
# Output returns all data assembled in the Builder as a byte string (bytes), ready for saving or transmission.
buf = builder.Output()

# Deserialization.
# GetRootAsPerson is a static method that interprets the buffer as a Person object.
# The first argument is the buffer (buf) and the second is the offset (0) indicating where to start reading (usually 0 for the root object).
person_msg = Person.Person.GetRootAsPerson(buf, 0)

# Extract the name field from the deserialized object.
# Name() returns the string as bytes since FlatBuffers stores strings in UTF-8.
# decode("utf-8") converts the bytes into a Python string, which is good practice even if "Pawel" is ASCII.
name = person_msg.Name().decode("utf-8")  

# Extract the age field from the deserialized object.
# Age() returns the int value directly, as it is a primitive type stored in the buffer in its ready-to-use form.
age = person_msg.Age()

print("Name:", name)
print("Age:", age)
```

---

### Performance

- **Protobuf**:
    - Typically produces small message sizes due to using varint encoding for integers.
    - Requires parsing, which creates additional structures in memory. This might not be critical for microservices but can be noticeable in resource-intensive applications.
    - Performs well when used with gRPC.

- **FlatBuffers**:
    - Zero-copy deserialization makes it extremely fast for frequent data access.
    - Reduces memory usage by eliminating extra data copying.
    - In large game engines and mobile applications, this approach offers significant speed and memory consumption advantages.

---

### Additional Aspects

1. **Security**:
    - Protobuf ignores unknown fields, which can be beneficial (does not break older code) but may make it harder to detect extraneous or malicious data.
    - FlatBuffers works with pointers (offsets) within the buffer; it is crucial to ensure the data is not corrupted to prevent out-of-bound access during reading.

2. **Readability**:
    - Both formats are binary by default and not human-readable.
    - Tools exist to convert them to a JSON-like format for debugging and testing.

3. **RPC**:
    - Protobuf has built-in support in gRPC (service and method definitions in `.proto` files).
    - FlatBuffers is not tied to any specific RPC framework; third-party solutions or custom frameworks can be used.

4. **Special Types**:
    - Protobuf includes well-known types (e.g., `Timestamp`, `Duration`, etc.).
    - In FlatBuffers, you may need to define custom types for dates, time, and similar data.

---

### In Summary

- **Protobuf**:
    - Ideal for microservices, network RPC, and projects where gRPC integration and broad language support are important.
    - Offers a more "classic" and easy-to-learn approach to serialization.

- **FlatBuffers**:
    - Particularly useful when every byte of memory is critical (such as in games, VR/AR, mobile applications) and when extremely fast access to any field without unpacking the entire message is required.
    - Suitable for tasks that involve serializing/deserializing very large volumes of data with minimal overhead.

Thus, the choice between Protobuf and FlatBuffers depends on performance requirements, memory constraints, integration with existing tools, and schema evolution needs. Both formats have proven effective, though they offer different strengths and trade-offs.
