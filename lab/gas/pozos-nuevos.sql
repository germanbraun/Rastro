-- Estudio de factibilidad de gas de Vaca Muerta (docs/lab-gas-vaca-muerta.md): pozos nuevos y su gas de 6 y 12 meses.
-- Correr con: docker exec -i rastro-postgres-1 psql -U rastro < lab/gas/pozos-nuevos.sql
-- Producción por pozo y mes, solo formación vaca muerta.
create temp table m as
select idpozo, make_date(anio,mes,1) f, sum(prod_gas) gas, sum(prod_pet) pet,
  max(tipopozo) tipopozo, max(sub_tipo_recurso) sub, max(formacion) formacion,
  max(empresa) empresa, max(idareapermisoconcesion) conc, max(areapermisoconcesion) concnom
from (select * from capitulo4.produccion union all select * from capitulo4.produccion_historica) t
where formacion='vaca muerta'
group by 1,2;
create index on m(idpozo,f);
analyze m;
create temp table p as
select idpozo, min(f) primera_fila, min(f) filter (where gas>0 or pet>0) inicio, max(sub) sub
from m group by 1;
create temp table n as
select p.idpozo, p.inicio, extract(year from p.inicio)::int anio, mi.tipopozo, mi.empresa, mi.conc, mi.concnom,
 (p.primera_fila < p.inicio) filas_previas,
 sum(x.gas) filter (where x.f < p.inicio + interval '6 months') g6,
 sum(x.gas) filter (where x.f < p.inicio + interval '12 months') g12,
 sum(x.pet) filter (where x.f < p.inicio + interval '12 months') p12,
 sum(x.gas) filter (where x.f >= p.inicio + interval '1 month' and x.f < p.inicio + interval '7 months') g6b,
 count(*) filter (where x.f < p.inicio + interval '12 months' and x.gas=0) meses_cero12,
 p.inicio + interval '5 months' <= date '2025-12-01' tiene6,
 p.inicio + interval '11 months' <= date '2025-12-01' tiene12
from p join m mi on mi.idpozo=p.idpozo and mi.f=p.inicio
join m x on x.idpozo=p.idpozo and x.f >= p.inicio
where p.sub='SHALE' and p.inicio > date '2023-01-01'
group by 1,2,3,4,5,6,7,8;
-- Pozos nuevos: se descartan los que ya figuraban en enero de 2023 con producción cero (pozos viejos reactivados).
create temp table l as select n.* from n join p using(idpozo) where not (p.primera_fila='2023-01-01' and n.filas_previas);
select anio, tipopozo, count(*), count(*) filter (where tiene6) con6, count(*) filter (where tiene12) con12 from l group by 1,2 order by 1,2;
