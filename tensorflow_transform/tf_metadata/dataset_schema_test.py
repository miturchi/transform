# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for dataset_metadata.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pickle

import tensorflow as tf

from tensorflow_transform.tf_metadata import dataset_schema as sch
from tensorflow_transform.tf_metadata import test_common
import unittest


class DatasetSchemaTest(unittest.TestCase):

  def test_feature_spec_roundtrip(self):
    schema = sch.from_feature_spec(test_common.test_feature_spec)
    generated_feature_spec = schema.as_feature_spec()
    self.assertEqual(test_common.test_feature_spec, generated_feature_spec)


  def test_sequence_feature_not_supported(self):
    feature_spec = {
        # FixedLenSequenceFeatures
        'fixed_seq_bool':
            tf.FixedLenSequenceFeature(shape=[10], dtype=tf.bool),
        'fixed_seq_bool_allow_missing':
            tf.FixedLenSequenceFeature(
                shape=[5], dtype=tf.bool, allow_missing=True),
        'fixed_seq_int':
            tf.FixedLenSequenceFeature(shape=[5], dtype=tf.int64),
        'fixed_seq_float':
            tf.FixedLenSequenceFeature(shape=[5], dtype=tf.float32),
        'fixed_seq_string':
            tf.FixedLenSequenceFeature(shape=[5], dtype=tf.string),
    }

    with self.assertRaisesRegexp(ValueError,
                                 'DatasetSchema does not support '
                                 'FixedLenSequenceFeature yet.'):
      sch.from_feature_spec(feature_spec)

  def test_manually_create_schema(self):
    schema = test_common.get_manually_created_schema()
    generated_feature_spec = schema.as_feature_spec()
    self.assertEqual(test_common.test_feature_spec, generated_feature_spec)

  def test_domain_picklable(self):
    domain = sch.dtype_to_domain(tf.float32)
    domain_new = pickle.loads(pickle.dumps(domain))

    self.assertEqual(type(domain), type(domain_new))
    self.assertEqual(domain.dtype, domain_new.dtype)

  def test_infer_column_schema_from_tensor(self):
    dense = tf.constant([[1., 2.], [3., 4.]], dtype=tf.float32, shape=[2, 2])
    column_schema = sch.infer_column_schema_from_tensor(dense)
    expected_column_schema = sch.ColumnSchema(
        sch.LogicalColumnSchema(sch.dtype_to_domain(tf.float32),
                                sch.LogicalShape([sch.Axis(2)])),
        sch.FixedColumnRepresentation())
    self.assertEqual(expected_column_schema, column_schema)

    varlen = tf.sparse_placeholder(tf.string)
    column_schema = sch.infer_column_schema_from_tensor(varlen)
    expected_column_schema = sch.ColumnSchema(
        sch.LogicalColumnSchema(sch.dtype_to_domain(tf.string),
                                sch.LogicalShape([sch.Axis(None)])),
        sch.ListColumnRepresentation())
    self.assertEqual(expected_column_schema, column_schema)

  def test_schema_equality(self):
    schema1 = sch.Schema(column_schemas={
        'fixed_bool_with_default': sch.ColumnSchema(
            sch.LogicalColumnSchema(sch.dtype_to_domain(tf.bool),
                                    sch.LogicalShape([sch.Axis(1)])),
            sch.FixedColumnRepresentation(False)),
        'var_float': sch.ColumnSchema(
            sch.LogicalColumnSchema(sch.dtype_to_domain(tf.float32),
                                    sch.LogicalShape([sch.Axis(None)])),
            sch.ListColumnRepresentation())
    })
    schema2 = sch.Schema(column_schemas={
        'fixed_bool_with_default': sch.ColumnSchema(
            sch.LogicalColumnSchema(sch.dtype_to_domain(tf.bool),
                                    sch.LogicalShape([sch.Axis(1)])),
            sch.FixedColumnRepresentation(False)),
        'var_float': sch.ColumnSchema(
            sch.LogicalColumnSchema(sch.dtype_to_domain(tf.float32),
                                    sch.LogicalShape([sch.Axis(None)])),
            sch.ListColumnRepresentation())
    })
    schema3 = sch.Schema(column_schemas={
        'fixed_bool_with_default': sch.ColumnSchema(
            sch.LogicalColumnSchema(sch.dtype_to_domain(tf.bool),
                                    sch.LogicalShape([sch.Axis(1)])),
            sch.FixedColumnRepresentation(False)),
        'var_float': sch.ColumnSchema(
            sch.LogicalColumnSchema(sch.dtype_to_domain(tf.float64),
                                    sch.LogicalShape([sch.Axis(None)])),
            sch.ListColumnRepresentation())
    })
    schema4 = sch.Schema(column_schemas={
        'fixed_bool_with_default': sch.ColumnSchema(
            sch.LogicalColumnSchema(sch.dtype_to_domain(tf.bool),
                                    sch.LogicalShape([sch.Axis(1)])),
            sch.FixedColumnRepresentation(False))
    })

    self.assertEqual(schema1, schema2)
    self.assertNotEqual(schema1, schema3)
    self.assertNotEqual(schema1, schema4)

  def test_column_schema_equality(self):
    c1 = sch.ColumnSchema(
        sch.LogicalColumnSchema(sch.dtype_to_domain(tf.bool),
                                sch.LogicalShape([sch.Axis(1)])),
        sch.FixedColumnRepresentation(False))
    c2 = sch.ColumnSchema(
        sch.LogicalColumnSchema(sch.dtype_to_domain(tf.bool),
                                sch.LogicalShape([sch.Axis(1)])),
        sch.FixedColumnRepresentation(False))
    c3 = sch.ColumnSchema(
        sch.LogicalColumnSchema(sch.dtype_to_domain(tf.bool),
                                sch.LogicalShape([sch.Axis(1)])),
        sch.FixedColumnRepresentation())
    c4 = sch.ColumnSchema(
        sch.LogicalColumnSchema(sch.dtype_to_domain(tf.bool),
                                sch.LogicalShape([sch.Axis(2)])),
        sch.FixedColumnRepresentation())

    self.assertEqual(c1, c2)
    self.assertNotEqual(c1, c3)
    self.assertNotEqual(c3, c4)

  def test_logical_column_schema_equality(self):
    c1 = sch.LogicalColumnSchema(
        sch.dtype_to_domain(tf.int64),
        sch.LogicalShape([sch.Axis(5), sch.Axis(6), sch.Axis(7)]))
    c2 = sch.LogicalColumnSchema(
        sch.dtype_to_domain(tf.int64),
        sch.LogicalShape([sch.Axis(5), sch.Axis(6), sch.Axis(7)]))
    c3 = sch.LogicalColumnSchema(
        sch.dtype_to_domain(tf.int32),
        sch.LogicalShape([sch.Axis(5), sch.Axis(6), sch.Axis(7)]))
    c4 = sch.LogicalColumnSchema(
        sch.dtype_to_domain(tf.int64),
        sch.LogicalShape(None))

    self.assertEqual(c1, c2)
    self.assertNotEqual(c1, c3)
    self.assertNotEqual(c3, c4)

  def test_domain_equality(self):
    d1 = sch.dtype_to_domain(tf.int64)
    d2 = sch.dtype_to_domain(tf.int64)
    d3 = sch.dtype_to_domain(tf.int32)
    d4 = sch.dtype_to_domain(tf.bool)

    self.assertEqual(d1, d2)
    self.assertNotEqual(d1, d3)
    self.assertNotEqual(d3, d4)

  def test_logical_shape_equality(self):
    s1 = sch.LogicalShape([sch.Axis(1), sch.Axis(2)])
    s2 = sch.LogicalShape([sch.Axis(1), sch.Axis(2)])
    s3 = sch.LogicalShape([sch.Axis(0)])
    s4 = sch.LogicalShape(None)

    self.assertEqual(s1, s2)
    self.assertNotEqual(s1, s3)
    self.assertNotEqual(s3, s4)

  def test_axis_equality(self):
    a1 = sch.Axis(0)
    a2 = sch.Axis(0)
    a3 = sch.Axis(None)

    self.assertEqual(a1, a2)
    self.assertNotEqual(a1, a3)

  def test_column_representation_equality(self):
    fixed1 = sch.FixedColumnRepresentation(1.1)
    fixed2 = sch.FixedColumnRepresentation(1.1)
    fixed3 = sch.FixedColumnRepresentation()

    list1 = sch.ListColumnRepresentation()
    list2 = sch.ListColumnRepresentation()

    sparse1 = sch.SparseColumnRepresentation(
        'val', [sch.SparseIndexField('idx1', False),
                sch.SparseIndexField('idx2', True)])
    sparse2 = sch.SparseColumnRepresentation(
        'val', [sch.SparseIndexField('idx1', False),
                sch.SparseIndexField('idx2', True)])
    sparse3 = sch.SparseColumnRepresentation(
        'val', [sch.SparseIndexField('idx1', False),
                sch.SparseIndexField('idx2', False)])

    self.assertEqual(fixed1, fixed2)
    self.assertNotEqual(fixed1, fixed3)
    self.assertNotEqual(fixed1, list1)
    self.assertNotEqual(fixed1, sparse1)

    self.assertEqual(list1, list2)
    self.assertNotEqual(list1, sparse1)

    self.assertEqual(sparse1, sparse2)
    self.assertNotEqual(sparse1, sparse3)

  def test_sparse_index_field_equality(self):
    f1 = sch.SparseIndexField('foo', False)
    f2 = sch.SparseIndexField('foo', False)
    f3 = sch.SparseIndexField('bar', False)

    self.assertEqual(f1, f2)
    self.assertNotEqual(f2, f3)


if __name__ == '__main__':
  unittest.main()
