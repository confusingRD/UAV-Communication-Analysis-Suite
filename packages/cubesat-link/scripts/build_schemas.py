"""Generate the portable Draft 2020-12 contracts; no third-party dependency."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def obj(properties, required=None, extra=False):
    return {'type':'object','properties':properties,
            'required':list(properties) if required is None else required,'additionalProperties':extra}


def ref(name):
    return {'$ref':'#/$defs/'+name}


def array(item, minimum=0, maximum=None):
    result = {'type':'array','items':item,'minItems':minimum}
    if maximum is not None:
        result['maxItems'] = maximum
    return result


def main():
    number = {'type':'number'}
    positive = dict(number,exclusiveMinimum=0)
    nonnegative = dict(number,minimum=0)
    text = {'type':'string','minLength':1}
    boolean = {'type':'boolean'}
    nullable_number = {'type':['number','null']}
    nullable_bool = {'type':['boolean','null']}
    defs = {}
    defs['earth'] = {'oneOf':[obj({'model':{'const':'WGS84'}}),
                                      obj({'model':{'const':'sphere'},'radius_m':positive})]}
    defs['station'] = obj({'lat_deg':dict(number,minimum=-90,maximum=90),
                           'lon_deg':dict(number,minimum=-180,maximum=180),
                           'altitude_m':nonnegative,'min_elevation_deg':dict(number,minimum=0,maximum=90)},
                          ['lat_deg','lon_deg','altitude_m'])
    defs['state'] = obj({'position_m':array(number,3,3),'frame':{'const':'ECEF'},'epoch_utc':text})
    defs['metadata'] = obj({'source':text,'version':text,'epoch_utc':text,'applicability':text,
                            'units':dict(obj({},[],text),minProperties=1),
                            'temporal_kind':{'enum':['observation','reference','synthetic']}})
    defs['profile'] = obj({'height_m':array(nonnegative,2),'refractive_index':array(dict(number,minimum=1),2),
                           'source':text,'frequency_range_hz':array(positive,2,2),
                           'gamma_db_per_km':array(nonnegative,2),'gas_frequency_hz':positive,'gas_source':text,
                           'outside':{'enum':['vacuum_above_top','unavailable']}},
                          ['height_m','refractive_index','source','frequency_range_hz','outside'])
    defs['neutral'] = {'oneOf':[obj({'kind':{'const':'p834_reference'}}),
                               obj({'kind':{'const':'table'},'profile':ref('profile'),'metadata':ref('metadata')})]}
    defs['binding'] = obj({'station':ref('station'),'state':ref('state'),'earth':ref('earth'),
                           'path_kind':{'enum':['straight','spherical_refracted']},'path_length_m':positive})
    defs['electron_path'] = obj({'distance_m':array(nonnegative,2),'density_per_m3':array(nonnegative,2),
                                 'source':text,'b_parallel_t':array(number,2)},
                                ['distance_m','density_per_m3','source'])
    defs['tec'] = obj({'electrons_per_m2':nonnegative,'path_length_m':positive,'source':text,
                       'ne_b_integral':number},['electrons_per_m2','path_length_m','source'])
    defs['electrons'] = {'oneOf':[obj({'kind':{'const':kind},'data':ref(data),
                                       'metadata':ref('metadata'),'binding':ref('binding')})
                                  for kind,data in [('path','electron_path'),('tec','tec')]]}
    defs['effect'] = {'oneOf':[
        obj({'value':{'type':'null'},'unit':text,'status':{'const':'not_computable'},'reason':text}),
        obj({'value':number,'unit':text,'status':{'enum':['computed','assumed']},'reason':text})]}
    names = ['free_space','gas','rain','cloud','neutral_scintillation','ionospheric_scintillation',
             'ionospheric_absorption','beam_spreading','polarization']
    defs['losses'] = obj({k:ref('effect') for k in names})
    defs['supplied_losses'] = obj({k:ref('effect') for k in names if k!='free_space'},[])
    radio = {k:number for k in ('tx_power_dbm','tx_gain_dbi','rx_gain_dbi','receiver_threshold_dbm')}
    radio.update({k:nonnegative for k in ('tx_pointing_loss_db','rx_pointing_loss_db','cable_loss_db','required_margin_db')})
    radio.update(receiver_mode=text,antenna_basis=text)
    defs['radio'] = obj(radio,[k for k in radio if k!='required_margin_db'])
    defs['polarization'] = obj({'tx':{'enum':['linear','circular']},'rx':{'enum':['linear','circular']},
                                'alignment_rad':number,'circular_match':boolean},['tx','rx'])
    common = {'schema_version':{'const':'1.0'},'earth':ref('earth'),'station':ref('station')}
    evaluate = dict(common,operation={'const':'evaluate_link'},state=ref('state'),frequency_hz=positive,
                    vacuum=boolean,radio=ref('radio'),polarization=ref('polarization'),neutral=ref('neutral'),
                    electrons=ref('electrons'),supplied_losses=ref('supplied_losses'))
    windows = dict(common,operation={'const':'contact_windows'},states=array(ref('state'),2),
                   max_gap_s=positive,mode={'const':'geometric'})
    request = {'$schema':'https://json-schema.org/draft/2020-12/schema',
               'title':'cubesat-link request 1.0','$defs':defs,
               'oneOf':[obj(evaluate,list(common)+['operation','state','frequency_hz']),
                        obj(windows,list(common)+['operation','states'])]}
    defs['geometry'] = obj({'slant_range_m':positive,'azimuth_deg':nullable_number,'elevation_deg':number,
                            'earth_occulted':boolean,'above_mask':boolean,'geometric_visible':boolean,'earth_model':text})
    ray = {k:nullable_number for k in ('apparent_elevation_deg','path_length_m','excess_path_m','bending_deg',
                                       'max_central_angle_deg','endpoint_residual_rad','refractivity_excess_m',
                                       'geometric_excess_m','total_excess_m')}
    ray.update(status={'enum':['computed','not_computable']},reason=text,gas_loss=ref('effect'),ground_clear=nullable_bool)
    defs['ray'] = obj(ray)
    defs['budget'] = obj({'received_power_dbm':ref('effect'),'margin_db':ref('effect'),
                          'meets_required_margin':nullable_bool,'hardware_db':obj({},[],number),
                          'throughput_bps':ref('effect'),'radio_assumptions':obj({},[],text)})
    defs['provider_record'] = obj(dict(defs['metadata']['properties'],status={'enum':['computed','not_computable']},reason=text))
    defs['link_result'] = obj({'geometry':ref('geometry'),
                              'neutral_ray':{'anyOf':[{'type':'null'},ref('ray')]},
                              'refracted_visible':nullable_bool,'path_available':nullable_bool,'path_basis':text,
                              'losses_db':ref('losses'),
                              'ionosphere':obj({k:ref('effect') for k in ('slant_tec','group_delay','phase_path',
                                  'phase_advance','faraday_rotation','scintillation','absorption','ray_deflection')}),
                              'neutral_excess_delay_s':ref('effect'),'budget':ref('budget'),
                              'providers':obj({},[],ref('provider_record'))})
    defs['window'] = obj({'start_utc':text,'end_utc':text,'start_clipped':boolean,'end_clipped':boolean,'method':text})
    defs['window_result'] = obj({'windows':array(ref('window')),'mode':{'const':'geometric'},'earth':ref('earth')})
    envelope = {'schema_version':{'const':'1.0'},'release':text,'ok':{'const':True}}
    response = {'$schema':'https://json-schema.org/draft/2020-12/schema',
                'title':'cubesat-link response 1.0','$defs':defs,'oneOf':[
                    obj(dict(envelope,operation={'const':'evaluate_link'},result=ref('link_result'))),
                    obj(dict(envelope,operation={'const':'contact_windows'},result=ref('window_result'))),
                    obj({'schema_version':{'const':'1.0'},'release':text,'ok':{'const':False},
                         'error':obj({'code':{'enum':['INVALID_JSON','SCHEMA_ERROR','UNSUPPORTED_SCHEMA',
                                                     'INVALID_INPUT','IO_ERROR','INTERNAL_ERROR']},
                                      'message':text,'path':text})})]}
    for name,data in [('request',request),('response',response)]:
        content = json.dumps(data,indent=2)+'\n'
        (ROOT/'cubesat_link'/f'{name}.schema.json').write_text(content,encoding='utf-8')
        (ROOT/'schemas').mkdir(exist_ok=True)
        (ROOT/'schemas'/f'{name}.schema.json').write_text(content,encoding='utf-8')


if __name__=='__main__':
    main()
