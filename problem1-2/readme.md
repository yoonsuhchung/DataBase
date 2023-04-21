#SQL parser의 확장을 통한 DBMS 일부 구현(DDL, DML)

##스키마 설계

과제 스펙에 명시된 바와 같이 스키마 설계 및 관리 방법에는 다음과 같은 것들이 있습니다.

1.	하나의 DB파일에 하나의 스키마를 관리하는 방법 (One DB-One Schema)
2.	하나의 DB파일에 복수의 스키마를 관리하는 방법 (One DB-Multi Schema)
3.	스키마의 메타데이터를 별도의 DB파일에 저장, 관리하는 방법 (Metadata Schema) 
저는 2번과 같이 하나의 DB파일에서 복수의 스키마를 관리하는 방법을 채택하였습니다. Python의 pickle 라이브러리를 사용하면 dictionary 자료형을 byte string으로 변환할 수 있고, 또 byte string을 다시 dictionary 형태로 변환할 수 있습니다. 이를 활용하여 db에 저장되는 key와 value를 모두 dictionary 형태로 구현하였습니다. BerkeleyDb에 저장되는 record는 크게 두 가지 종류로 분류됩니다.

Ex) Table schema가 저장되는 형태

Key: {‘table’: table_name}
Value: {column_name: {‘type’: (‘char’, 15), ‘notnull’: 0, ‘pk’=0, ‘fk’=ref_table_name},
	Column_name2: {‘type’: (‘int’, None), ‘notnull’: 1, ‘pk’=1, ‘fk’=None}, …}

Ex) Record가 저장되는 형태
Key: {‘record: table_name}
Value: {column_name: [‘Lucy’, ‘Charles’, ‘James’, … ],
	Column_name2: [30, 15, 17, …], …}

##알고리즘

Schema 설계에 맞도록 각 DDL과 DML을 구현하였습니다. 우선 CREATE TABLE의 경우, table schema와 empty record를 생성해 주었습니다. 파싱된 결과를 바탕으로 schema에 column의 type과 constraint에 관한 정보를 생성한 뒤 INSERT 등 DML 구현을 위해 column들에 해당하는 empty list를 dictionary에 넣어 주었습니다. DROP TABLE에서는 schema와 record 모두를 지워 주었습니다. 이때 이미 참조하고 있는 테이블을 삭제했을 때는 오류가 발생해야 하기 때문에, cursor를 이용해 루프를 돌며 각 table schema에서 해당 테이블의 참조 여부를 확인하였습니다. 

DB는 가장 처음에 run.py와 같은 경로에 지정해둔 이름의 db 파일이 없는 경우 생성됨과 동시에 열립니다. 만약 같은 경로에 해당 db가 이미 있는 경우, 그 db 파일을 사용합니다. 따라서 프로그램이 종료되어도 data가 날아가지 않는 persistent data를 구현할 수 있습니다.

##느낀 점 및 기타사항

늘 relational database에만 익숙해져 있다가 key, value pair로만 저장할 수 있는 DBMS를 구현하라고 하니, 각 command를 구현할 때마다 key와 value의 dictionary 구조를 바꾸는 등 난항을 겪었습니다. 이번 과제와 같이 구조화된 SQL의 경우 Relational Database가 dominant할 수밖에 없는 이유를 배울 수 있었고, BerkeyleyDB api를 활용하여 코드를 짜며 DBMS의 작동 원리 및 역할을 배웠습니다. 처음에는 Key-value pair로 저장된다고 하여 column-record 형식으로 넣어주는 방식이라고 단순하게 생각했었는데 key가 unique해야 하므로 한 파일에서 스키마와 레코드 모두를 관리하는 방식을 생각해 내는 것이 challenging했던 것 같습니다.

![image](https://user-images.githubusercontent.com/110687290/233727212-a89d207b-5bf5-468f-888d-725e1c94b72d.png)
